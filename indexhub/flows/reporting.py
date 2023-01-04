import io
from datetime import datetime
from hashlib import md5
from typing import List, Mapping, Optional

import boto3
import numpy as np
import polars as pl
from prefect import flow, task


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


@flow
def prepare_past_review_report(
    s3_data_bucket: str,
    s3_artifact_bucket: str,
    ftr_data_paths: Mapping[str, str],
    forecast_data_paths: Mapping[str, str],
    merged_entity_id: str,
    time_col: str,
):
    # 1. Load ftr actual, ftr manual, and backtests
    ftr_panel = load_data(s3_bucket=s3_data_bucket, s3_path=ftr_data_paths["actual"])
    ftr_panel_manual = None
    if "manual" in list(ftr_data_paths.keys()):
        ftr_panel_manual = load_data(
            s3_bucket=s3_data_bucket, s3_path=ftr_data_paths["manual"]
        )
    backtests = load_data(
        s3_bucket=s3_artifact_bucket, s3_path=forecast_data_paths["backtests"]
    )
    # 2. Add quantile column to ftr actual and ftr manual
    quantiles = get_quantiles_list(backtests)

    transf_ftr_panel = add_quantile_col(df=ftr_panel, quantiles=quantiles)
    transf_ftr_panel_manual = (
        add_quantile_col(df=ftr_panel_manual, quantiles=quantiles)
        if ftr_panel_manual is not None
        else None
    )

    # 3. Merge ftr actual, ftr manual, and backtests
    rpt_past_review = backtests.join(
        transf_ftr_panel,
        on=[merged_entity_id, time_col, "quantile"],
        how="outer",
    )
    if ftr_panel_manual is not None:
        rpt_past_review = rpt_past_review.join(
            transf_ftr_panel_manual,
            on=[merged_entity_id, time_col, "quantile"],
            how="outer",
        )

    # 4. Split merged entity cols and cast to categorical
    rpt_past_review = (
        split_merged_entity_cols(rpt_past_review, merged_entity_id)
        .pipe(cast_entity_cols_to_categorical, merged_entity_id)
        .drop("is_holiday")
    )

    paths = {
        "rpt_past_review": export_report(
            rpt_past_review,
            s3_artifact_bucket,
            forecast_data_paths["backtests"],
            suffix="rpt_past_review",
        )
    }
    return paths


@task
def split_merged_entity_cols(df: pl.LazyFrame, merged_entity_id: str) -> pl.LazyFrame:
    new_entity_cols = merged_entity_id.split(":")

    df_new = (
        df.collect()
        .with_columns(pl.col(merged_entity_id).str.split(":"))
        # Split the merged entity col into separated columns
        .with_column(
            pl.struct(
                [
                    pl.col(merged_entity_id).arr.get(i).alias(f"{col}")
                    for i, col in enumerate(new_entity_cols)
                ]
            ).alias(merged_entity_id),
        )
        .unnest(merged_entity_id)
    )

    return df_new.lazy()


@task
def cast_entity_cols_to_categorical(
    df: pl.LazyFrame, merged_entity_id: str
) -> pl.LazyFrame:
    new_entity_cols = merged_entity_id.split(":")
    df_new = df.with_columns(
        [pl.col(col).cast(pl.Categorical) for col in new_entity_cols]
    )
    return df_new


@flow
def prepare_metrics_report(
    s3_artifact_bucket: str,
    forecast_data_paths: Mapping[str, str],
    merged_entity_id: str,
):
    # 1. Load metrics from forecast data
    metrics = load_data(
        s3_bucket=s3_artifact_bucket, s3_path=forecast_data_paths["metrics"]
    )

    # 2. Split entity id into list of cols and cast entity cols to categorical
    rpt_metrics = split_merged_entity_cols(metrics, merged_entity_id).pipe(
        cast_entity_cols_to_categorical, merged_entity_id
    )

    paths = {
        "rpt_metrics": export_report(
            rpt_metrics,
            s3_artifact_bucket,
            forecast_data_paths["metrics"],
            suffix="rpt_metrics",
        )
    }

    return paths


@flow
def prepare_forecast_report(
    s3_data_bucket: str,
    s3_artifact_bucket: str,
    ftr_data_paths: Mapping[str, str],
    forecast_data_paths: Mapping[str, str],
    merged_entity_id: str,
    target_col: str,
    time_col: str,
):
    # 1. Load ftr actual, ftr manual, backtests, y_preds
    ftr_panel = load_data(s3_bucket=s3_data_bucket, s3_path=ftr_data_paths["actual"])
    ftr_panel_manual = None
    if "manual" in list(ftr_data_paths.keys()):
        ftr_panel_manual = load_data(
            s3_bucket=s3_data_bucket, s3_path=ftr_data_paths["manual"]
        )
    backtests = load_data(
        s3_bucket=s3_artifact_bucket, s3_path=forecast_data_paths["backtests"]
    )
    y_preds = load_data(
        s3_bucket=s3_artifact_bucket, s3_path=forecast_data_paths["y_preds"]
    )

    # 2. Add quantile column to ftr actual and ftr manual
    quantiles = get_quantiles_list(backtests)
    transf_ftr_panel = add_quantile_col(df=ftr_panel, quantiles=quantiles)
    transf_ftr_panel_manual = (
        add_quantile_col(df=ftr_panel_manual, quantiles=quantiles)
        if ftr_panel_manual is not None
        else None
    )

    # 3. Join ftr_actual, backtests, and y_preds into single df
    rpt_forecast = backtests.join(
        transf_ftr_panel, on=[merged_entity_id, time_col, "quantile"], how="outer"
    ).join(
        y_preds,
        on=[merged_entity_id, time_col, "quantile", f"{target_col}:forecast"],
        how="outer",
    )

    if ftr_panel_manual is not None:
        rpt_forecast = rpt_forecast.join(
            transf_ftr_panel_manual,
            on=[merged_entity_id, time_col, "quantile"],
            how="outer",
        )

    # 4. Split entity id into list of cols, cast entity cols to categorical and drop is_holiday
    rpt_forecast = (
        split_merged_entity_cols(rpt_forecast, merged_entity_id)
        .pipe(cast_entity_cols_to_categorical, merged_entity_id)
        .drop("is_holiday")
    )

    paths = {
        "rpt_forecast": export_report(
            rpt_forecast,
            s3_artifact_bucket,
            forecast_data_paths["y_preds"],
            suffix="rpt_forecast",
        )
    }
    return paths


@task
def assign_month_year(
    df: pl.LazyFrame,
    time_col: str,
) -> pl.LazyFrame:
    df_new = df.collect().with_columns(
        (
            pl.col(time_col).dt.strftime("%b")
            + " "
            + pl.col(time_col).dt.strftime("%Y")
        ).alias("month_year")
    )
    return df_new.lazy()


@task
def transform_target_col_to_wide_format(
    y_preds: pl.LazyFrame,
    target_col: str,
    merged_entity_id: str,
    time_col: str,
    quantiles: List[int],
):
    df_new = (
        # Filter dataframe to only specific quantiles
        y_preds.collect()
        # Unstack quantiles to columns
        .pivot(
            index=[merged_entity_id, time_col],
            columns="quantile",
            values=target_col,
        )
        .with_columns(
            # Rename target_col with quantile as suffix
            [
                pl.col(f"{quantile}").alias(f"{target_col}_{quantile}")
                for quantile in quantiles
            ]
        )
        .drop([str(quantile) for quantile in quantiles])
    )
    return df_new.lazy()


@flow
def prepare_forecast_scenario_report(
    s3_artifact_bucket: str,
    forecast_data_paths: Mapping[str, str],
    merged_entity_id: str,
    target_col: str,
    time_col: str,
):
    # 1. Load y_preds
    y_preds = load_data(
        s3_bucket=s3_artifact_bucket, s3_path=forecast_data_paths["y_preds"]
    )

    # 2. Identify the quantiles
    quantiles = get_quantiles_list(y_preds)

    # 3. Convert target col to wide, assign month_year, split merged entity id and cast to categorical
    rpt_forecast_scenario = (
        transform_target_col_to_wide_format(
            y_preds, f"{target_col}:forecast", merged_entity_id, time_col, quantiles
        )
        .pipe(assign_month_year, time_col)
        .pipe(split_merged_entity_cols, merged_entity_id)
        .pipe(cast_entity_cols_to_categorical, merged_entity_id)
    )

    paths = {
        "rpt_forecast_scenario": export_report(
            rpt_forecast_scenario,
            s3_artifact_bucket,
            forecast_data_paths["y_preds"],
            suffix="rpt_forecast_scenario",
        )
    }
    return paths


@task
def groupby_agg(
    df: pl.LazyFrame,
    target_col: str,
    merged_entity_id: str,
    agg_by: str,
) -> pl.DataFrame:
    agg_method = {"std": pl.std(target_col), "mean": pl.mean(target_col)}
    df_new = (
        df.groupby(merged_entity_id)
        .agg(agg_method[agg_by])
        .with_column(pl.col(target_col).alias(agg_by))
        .drop(target_col)
    )
    return df_new


@task
def filter_df_by_quantile(
    df: pl.LazyFrame, entity_cols: str, filter_col: str, quantile: int
) -> pl.LazyFrame:
    df_new = (
        df.collect()
        .filter(pl.col("quantile") == quantile)
        .with_column(pl.col(filter_col).round(2))
        .select([entity_cols, filter_col])
    )
    return df_new.lazy()


@task
def assign_cv_column(df: pl.LazyFrame, target_col: str) -> pl.LazyFrame:
    df_new = df.with_column(
        (pl.col("std") / pl.col("mean")).round(2).alias(f"{target_col}_cv")
    ).drop_nulls()
    return df_new.lazy()


@task
def assign_trendline_columns(df: pl.LazyFrame) -> pl.LazyFrame:
    # Use numpy to compute the slope and intercept
    slope, intercept = np.polyfit(
        df.collect()["quantity_cv"], df.collect()["smape:manual"], 1
    )
    df_new = df.with_columns(
        [
            # Compute the ratio of manual smape over cv
            (pl.col("smape:manual") / pl.col("quantity_cv"))
            .alias("manual_smape_over_cv")
            .round(2),
            # Compute the trendline value
            (slope * pl.col("quantity_cv") + intercept).alias("trendline").round(2),
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
def prepare_volatility_report(
    s3_data_bucket: str,
    s3_artifact_bucket: str,
    ftr_data_paths: Mapping[str, str],
    forecast_data_paths: Mapping[str, str],
    merged_entity_id: str,
    target_col: str,
):
    # Skip the report if the source does not have manual forecasts
    if "manual" in ftr_data_paths:
        # 1. Load ftr actual and metrics panels
        ftr_panel = load_data(
            s3_bucket=s3_data_bucket, s3_path=ftr_data_paths["actual"]
        )
        metrics = load_data(
            s3_bucket=s3_artifact_bucket, s3_path=forecast_data_paths["metrics"]
        )

        # 2. Prepare tables for coefficient of volatility and join tables
        ftr_panel_std = groupby_agg(
            ftr_panel, f"{target_col}:actual", merged_entity_id, agg_by="std"
        )
        ftr_panel_mean = groupby_agg(
            ftr_panel, f"{target_col}:actual", merged_entity_id, agg_by="mean"
        )
        smape_manual_metrics = filter_df_by_quantile(
            metrics, merged_entity_id, "smape:manual", quantile=0.5
        )
        rpt_volatility = (
            # Join mean, average and manual smape cols into single df
            ftr_panel_std.join(ftr_panel_mean, on=merged_entity_id).join(
                smape_manual_metrics, on=merged_entity_id
            )
        )

        # 3. Assign cv and trendline columns, split merged_entity_cols and cast to categorical
        rpt_volatility = (
            assign_cv_column(rpt_volatility, target_col)
            .pipe(assign_trendline_columns)
            .pipe(split_merged_entity_cols, merged_entity_id)
            .pipe(cast_entity_cols_to_categorical, merged_entity_id)
        )

        paths = {
            "rpt_volatility": export_report(
                rpt_volatility,
                s3_artifact_bucket,
                forecast_data_paths["metrics"],
                suffix="rpt_volatility",
            )
        }
    else:
        paths = {}
    return paths