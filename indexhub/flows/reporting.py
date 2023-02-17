import io
from datetime import datetime
from hashlib import md5
from typing import List, Mapping, Optional

import boto3
import numpy as np
import polars as pl
from prefect import flow, task
from pydantic import BaseModel

MODELS_TO_DESC = {
    "manual":"manual forecast",
    "lightgbm":"base AI model (no features)",
    "zero_inflated:lgbm":"zero inflated model (no features)",
    "ensemble":"ensemble model (no features)",
    "ensemble_add_weekend":"+ weekend",
    "ensemble_add_calendar":"+ calendar",
    "ensemble_add_holiday":"+ holiday",
    "ensemble_add_dummies":"+ dummies",
    "ensemble+manual":"AI + manual",
    "ensemble+manual+overrides_zero":"+ overrides zero",
}


class ReportingInput(BaseModel):
    s3_data_bucket: str
    s3_artifacts_bucket: str
    ftr_data_paths: Mapping[str, str]
    forecast_data_paths: Mapping[str, str]
    level_cols: List[str]


@task
def load_data(s3_bucket: str, s3_path: str) -> pl.LazyFrame:
    s3_client = boto3.resource("s3")
    s3_object = s3_client.Object(s3_bucket, s3_path)
    obj = s3_object.get()["Body"].read()
    data = pl.read_parquet(io.BytesIO(obj))
    return data.lazy()


@task
def export_report(
    df: pl.LazyFrame, s3_bucket: str, artifact_path: str, suffix: Optional[str] = None
) -> pl.LazyFrame:
    # Use first 7 characters of the hash of artifact path as ID
    identifer = md5(artifact_path.encode("utf-8")).hexdigest()[:7]
    ts = int(datetime.now().timestamp())
    s3_path = f"reports/{identifer}/{ts}"
    if suffix:
        s3_path = f"{s3_path}/{suffix}"
    df.collect().to_pandas().to_parquet(
        f"s3://{s3_bucket}/{s3_path}.parquet", index=False
    )
    return f"{s3_path}.parquet"


@task
def add_quantile_col(df: pl.LazyFrame, quantiles: List[str]) -> pl.LazyFrame:
    df_new = pl.concat(
        [
            df.collect().with_column(pl.lit(quantile).alias("quantile"))
            for quantile in quantiles
        ]
    )
    return df_new.lazy()


@task
def get_quantiles_list(df: pl.LazyFrame) -> List[int]:
    quantiles = (
        df.select(pl.col("quantile").unique())
        .collect()
        .get_column("quantile")
        .to_list()
    )
    return quantiles


@task
# Cast entity cols columns to string to join and concatenate dfs
def cast_entity_cols_to_str(
    df: pl.LazyFrame,
) -> pl.LazyFrame:
    df_new = df.with_columns(pl.col("^entity.*$").cast(pl.Utf8))

    return df_new


@task
def cast_entity_cols_to_categorical(
    df: pl.LazyFrame,
) -> pl.LazyFrame:
    df_new = df.with_columns(pl.col("^entity.*$").cast(pl.Categorical))

    return df_new


@task
def split_merged_entity_cols(df: pl.LazyFrame, level_cols: List[str]) -> pl.LazyFrame:
    df_new = (
        df.collect()
        .with_columns(pl.col("entity").str.split(":"))
        # Split the merged entity col into separated columns
        .with_column(
            pl.struct(
                [
                    pl.col("entity").arr.get(i).alias(f"entity_{i}")
                    for i, col in enumerate(level_cols)
                ]
            ).alias("entity"),
        )
        .unnest("entity")
    )

    return df_new.lazy()


@flow
def prepare_metrics_report(inputs: ReportingInput):
    # 1. Load metrics from forecast data
    metrics = (
        load_data(
            s3_bucket=inputs.s3_artifacts_bucket,
            s3_path=inputs.forecast_data_paths["metrics"],
        ).pipe(cast_entity_cols_to_str)
    )

    # 2. Split entity id into list of cols and cast entity cols to categorical
    rpt_metrics = split_merged_entity_cols(metrics, inputs.level_cols).pipe(
        cast_entity_cols_to_categorical
    )

    paths = {
        "rpt_metrics": export_report(
            rpt_metrics,
            inputs.s3_artifacts_bucket,
            inputs.forecast_data_paths["metrics"],
            suffix="rpt_metrics",
        )
    }

    return paths


@flow
def prepare_forecast_report(inputs: ReportingInput):
    # 1. Load ftr actual, ftr manual, backtests, y_preds
    ftr_panel = (
        load_data(
            s3_bucket=inputs.s3_data_bucket, s3_path=inputs.ftr_data_paths["actual"]
        ).pipe(cast_entity_cols_to_str)
    )
    ftr_panel_manual = (
            load_data(
            s3_bucket=inputs.s3_data_bucket, s3_path=inputs.ftr_data_paths["manual"]
        ).pipe(cast_entity_cols_to_str)
    )
    backtests = (
        load_data(
            s3_bucket=inputs.s3_artifacts_bucket,
            s3_path=inputs.forecast_data_paths["backtests"],
        ).pipe(cast_entity_cols_to_str)
    )
    y_preds = (
        load_data(
            s3_bucket=inputs.s3_artifacts_bucket,
            s3_path=inputs.forecast_data_paths["y_preds"],
        ).pipe(cast_entity_cols_to_str)
    )

    # 2. Add quantile column to ftr actual and ftr manual
    quantiles = get_quantiles_list(backtests)
    transf_ftr_panel = add_quantile_col(df=ftr_panel, quantiles=quantiles)
    transf_ftr_panel_manual = add_quantile_col(df=ftr_panel_manual, quantiles=quantiles)

    # 3. Join ftr_actual, backtests, and y_preds into single df
    rpt_forecast = (
        pl.concat([backtests, y_preds])
        .join(transf_ftr_panel, on=["entity", "time", "quantile"], how="outer")
        .join(
            transf_ftr_panel_manual,
            on=["entity", "time", "quantile"],
            how="outer",
        )
    )

    # 4. Split entity id into list of cols, cast entity cols to categorical and drop is_holiday
    rpt_forecast = (
        split_merged_entity_cols(rpt_forecast, inputs.level_cols)
        .pipe(cast_entity_cols_to_categorical)
        # Filter columns by entity, quantile, time and target cols
        .select([pl.col("^entity.*$"), "quantile", "time", pl.col("^target.*$")])
        .sort([pl.col("^entity.*$"), "quantile", "time"])
    )

    paths = {
        "rpt_forecast": export_report(
            rpt_forecast,
            inputs.s3_artifacts_bucket,
            inputs.forecast_data_paths["y_preds"],
            suffix="rpt_forecast",
        )
    }
    return paths


@task
def assign_month_year(
    df: pl.LazyFrame,
) -> pl.LazyFrame:
    df_new = df.collect().with_columns(
        (
            pl.col("time").dt.strftime("%b") + " " + pl.col("time").dt.strftime("%Y")
        ).alias("month_year")
    )
    return df_new.lazy()


@task
def transform_target_col_to_wide_format(
    y_preds: pl.LazyFrame,
    quantiles: List[int],
):
    values = [col for col in y_preds.columns if col in ["target:forecast", "target:forecast_overrides_zero"]]
    
    df_new = (
        # Filter dataframe to only specific quantiles
        y_preds.collect()
        # Unstack quantiles to columns
        .pivot(
            index=["entity", "time"],
            columns="quantile",
            values=values,
        )
    )

    if len(values) == 1:
        df_new = (
            df_new
             .with_columns(
            # Rename target_col with quantile as suffix
            [
                pl.col(f"{quantile}").alias(f"target:forecast_{quantile}")
                for quantile in quantiles
            ]
        )
        .drop([str(quantile) for quantile in quantiles])
        )
    return df_new.lazy()


@flow
def prepare_forecast_scenario_report(inputs: ReportingInput):
    # 1. Load y_preds
    y_preds = (
        load_data(
            s3_bucket=inputs.s3_artifacts_bucket,
            s3_path=inputs.forecast_data_paths["y_preds"],
        ).pipe(cast_entity_cols_to_str)
    )

    # 2. Identify the quantiles
    quantiles = get_quantiles_list(y_preds)

    # 3. Convert target col to wide, assign month_year, split merged entity id and cast to categorical
    rpt_forecast_scenario = (
        transform_target_col_to_wide_format(y_preds, quantiles)
        .pipe(assign_month_year)
        .pipe(split_merged_entity_cols, inputs.level_cols)
        .pipe(cast_entity_cols_to_categorical)
    )

    paths = {
        "rpt_forecast_scenario": export_report(
            rpt_forecast_scenario,
            inputs.s3_artifacts_bucket,
            inputs.forecast_data_paths["y_preds"],
            suffix="rpt_forecast_scenario",
        )
    }
    return paths


@task
def groupby_agg(
    df: pl.LazyFrame,
    agg_by: str,
) -> pl.DataFrame:
    agg_method = {"std": pl.std("target:actual"), "mean": pl.mean("target:actual")}
    df_new = (
        df.groupby("entity")
        .agg(agg_method[agg_by])
        .with_column(pl.col("target:actual").alias(agg_by))
        .drop("target:actual")
    )
    return df_new


@task
def filter_df_by_quantile(
    df: pl.LazyFrame, filter_col: str, quantile: int
) -> pl.LazyFrame:
    df_new = (
        df.collect()
        .filter(pl.col("quantile") == quantile)
        .with_column(pl.col(filter_col).round(2))
        .select(["entity", filter_col])
    )
    return df_new.lazy()


@task
def assign_cv_column(df: pl.LazyFrame) -> pl.LazyFrame:
    df_new = df.with_column(
        (pl.col("std") / pl.col("mean")).round(2).alias("target_cv")
    ).drop_nulls()
    return df_new.lazy()


@task
def assign_trendline_columns(df: pl.LazyFrame) -> pl.LazyFrame:
    # Use numpy to compute the slope and intercept
    slope, intercept = np.polyfit(
        df.collect()["target_cv"], df.collect()["smape:manual"], 1
    )
    df_new = df.with_columns(
        [
            # Compute the ratio of manual smape over cv
            (pl.col("smape:manual") / pl.col("target_cv"))
            .alias("manual_smape_over_cv")
            .round(2),
            # Compute the trendline value
            (slope * pl.col("target_cv") + intercept).alias("trendline").round(2),
        ]
    )
    # Compute the distance of manual smape to trendline
    df_new = (
        df_new.with_column(
            (pl.col("smape:manual") - pl.col("trendline")).alias(
                "distance_to_trendline"
            ),
        )
        # Drop unnecessary columns
        .drop(["smape:manual", "trendline", "std", "mean"])
    )
    # Assign column to indicate type of error
    df_new = df_new.with_column(
        pl.when(pl.col("distance_to_trendline") > 0)
        .then("Excess Error")
        .when(pl.col("distance_to_trendline") < 0)
        .then("Low Error")
        .otherwise(pl.lit("N/A"))
        .alias("over_under_trendline")
    )

    return df_new.lazy()


@flow
def prepare_volatility_report(inputs: ReportingInput):
    # 1. Load ftr actual and metrics panels
    ftr_panel = (
        load_data(
            s3_bucket=inputs.s3_data_bucket, s3_path=inputs.ftr_data_paths["actual"]
        ).pipe(cast_entity_cols_to_str)
    )
    metrics = (
        load_data(
            s3_bucket=inputs.s3_artifacts_bucket,
            s3_path=inputs.forecast_data_paths["metrics"],
        ).pipe(cast_entity_cols_to_str)
    )

    # 2. Prepare tables for coefficient of volatility and join tables
    ftr_panel_std = groupby_agg(ftr_panel, agg_by="std")
    ftr_panel_mean = groupby_agg(ftr_panel, agg_by="mean")
    smape_manual_metrics = filter_df_by_quantile(metrics, "smape:manual", quantile=0.5)
    rpt_volatility = (
        # Join mean, average and manual smape cols into single df
        ftr_panel_std.join(ftr_panel_mean, on="entity").join(
            smape_manual_metrics, on="entity"
        )
    )

    # 3. Assign cv and trendline columns, split merged_entity_cols and cast to categorical
    rpt_volatility = (
        assign_cv_column(rpt_volatility)
        .pipe(assign_trendline_columns)
        .pipe(split_merged_entity_cols, inputs.level_cols)
        .pipe(cast_entity_cols_to_categorical)
    )

    paths = {
        "rpt_volatility": export_report(
            rpt_volatility,
            inputs.s3_artifacts_bucket,
            inputs.forecast_data_paths["metrics"],
            suffix="rpt_volatility",
        )
    }

    return paths


def _get_outliers(inputs: ReportingInput) -> pl.LazyFrame:
    metrics = (
        load_data(
            s3_bucket=inputs.s3_artifacts_bucket,
            s3_path=inputs.forecast_data_paths["metrics"],
        ).pipe(cast_entity_cols_to_str)
    )

    outliers = (
        metrics
        .groupby(["entity", "quantile"])
        .agg(pl.col("mae_improvement_%").sum())
        .filter(pl.col("mae_improvement_%")<=0)
    )
    return outliers


@flow
def prepare_outliers_report(inputs: ReportingInput):
    rpt_outliers = (
        _get_outliers(inputs)
        .pipe(split_merged_entity_cols, inputs.level_cols)
        .pipe(cast_entity_cols_to_categorical)
    )
    paths = {
        "rpt_outliers": export_report(
            rpt_outliers,
            inputs.s3_artifacts_bucket,
            inputs.forecast_data_paths["metrics"],
            suffix="rpt_outliers",
        )
    }
    return paths


@flow
def prepare_uplift_report(inputs: ReportingInput):
    metrics_by_model = (
        load_data(
            s3_bucket=inputs.s3_artifacts_bucket,
            s3_path=inputs.forecast_data_paths["metrics_by_model"],
        ).pipe(cast_entity_cols_to_str)
    )

    outliers = (
        _get_outliers(inputs)
        .filter(pl.col("quantile")==0.5)
        .collect()
        .get_column("entity").to_list()
    )

    models_to_num = {model:i+1 for i, model in enumerate(MODELS_TO_DESC.keys())}

    rpt_uplift = (
        metrics_by_model
        .filter(~pl.col("entity").is_in(outliers))
        .filter(pl.col("model").is_in(list(MODELS_TO_DESC.keys())))
        .groupby("model", maintain_order=True)
        .agg(
            [
                # MAE
                pl.col("mae_improvement_%").mean().round(2).keep_name(), 
                # Under-forecast
                pl.col("underforecast_improvement_%").mean().round(2).keep_name(), 
                # Over-forecast
                pl.col("overforecast_improvement_%").mean().round(2).keep_name(), 
            ]
        )
        .select(
            [
                pl.col("model").apply(lambda x: models_to_num[x]).alias("no."),
                pl.col("model"),
                pl.col("model").apply(lambda x: MODELS_TO_DESC[x]).alias("desc"),
                pl.all().exclude("model"),
            ]
        )
        .sort("no.")
    )

    mae_improvement_new = rpt_uplift.select("mae_improvement_%").shift(periods=1).rename({"mae_improvement_%":"mae_improvement%_new"})
    underforecast_improvement_new = rpt_uplift.select("underforecast_improvement_%").shift(periods=1).rename({"underforecast_improvement_%":"underforecast_improvement%_new"})
    overforecast_improvement_new = rpt_uplift.select("overforecast_improvement_%").shift(periods=1).rename({"overforecast_improvement_%":"overforecast_improvement%_new"})

    rpt_uplift = (
        pl.concat(pl.collect_all([rpt_uplift, mae_improvement_new, underforecast_improvement_new, overforecast_improvement_new]), how="horizontal")
        .select(
            [
                pl.all().exclude(["mae_improvement%_new", "underforecast_improvement%_new", "overforecast_improvement%_new"]),
                (pl.col("mae_improvement_%") - pl.col("mae_improvement%_new")).alias("mae_improvement%_diff"),
                (pl.col("underforecast_improvement_%") - pl.col("underforecast_improvement%_new")).alias("underforecast_improvement%_diff"),
                (pl.col("overforecast_improvement_%") - pl.col("overforecast_improvement%_new")).alias("overforecast_improvement%_diff"),
            ]
        )
        .fill_null(0)
    ).lazy()

    paths = {
        "rpt_uplift": export_report(
            rpt_uplift,
            inputs.s3_artifacts_bucket,
            inputs.forecast_data_paths["metrics_by_model"],
            suffix="rpt_uplift",
        )
    }

    return paths
