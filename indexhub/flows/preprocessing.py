import io
import re
from datetime import datetime
from hashlib import md5
from typing import List, Mapping, Optional

import boto3
import polars as pl
from functime.feature_extraction.calendar import (
    add_calendar_effects,
    add_holiday_effects,
)
from functime.preprocessing import reindex_panel
from prefect import flow, task
from pydantic import BaseModel, validator
from typing_extensions import Literal

from indexhub.flows.forecasting import (
    DATE_FEATURES,
    MODEL_TO_SETTINGS,
    TEST_SIZE,
    add_weekend_effects,
    get_train_test_splits,
    run_backtest,
    run_forecast,
    transform_boolean_to_int,
    postproc,
    compute_metrics,
)

MIN_TRAIN_SIZE = {"3mo": 9, "1mo": 12, "1w": 18, "1d": 30}
BENCHMARK_MODELS = ["snaive"]


class PreprocessPanelInput(BaseModel):
    s3_bucket: str
    time_col: str
    entity_cols: List[str]
    freq: str
    raw_data_path: str
    source_id: str
    manual_forecast_path: Optional[str] = None
    filters: Optional[Mapping[str, List[str]]] = None


class PreprocessPanelOutput(BaseModel):
    actual: str
    manual: Optional[str] = None
    metadata: Mapping[str, str]


class PrepareHierarchicalPanelInput(BaseModel):
    s3_bucket: str
    level_cols: List[str]
    agg_method: Literal["sum", "mean"]
    fct_panel_path: str
    target_col: str
    freq: str
    lags: List[int]
    country_codes: Optional[List[str]] = None
    dummy_entity_cols: Optional[List[str]] = None
    manual_forecasts_path: Optional[str] = None
    allow_negatives: Optional[bool] = False

    @validator("manual_forecasts_path")
    def check_manual_forecasts_path(cls, v):
        return v or None

    @validator("allow_negatives")
    def check_allow_negatives(cls, v):
        return v or False


class PrepareHierarchicalPanelOutput(BaseModel):
    actual: str
    manual: str


def infer_dt_format(dt: str):
    n_chars = len(dt)
    if n_chars == 19:
        fmt = "%Y-%m-%d %H:%M:%S"
    elif n_chars == 10:
        fmt = "%Y-%m-%d"
    elif n_chars == 7:
        if "-" in dt:
            fmt = "%Y-%m"
    elif n_chars == 6:
        fmt = "%Y%m"
    else:
        raise ValueError(f"Failed to parse datetime: {dt}")
    return fmt


@task
def load_raw_panel(s3_bucket: str, s3_path: str) -> pl.LazyFrame:
    # io.BytesIO fails to change blanks to "#N/A"
    s3_client = boto3.resource("s3")
    s3_object = s3_client.Object(s3_bucket, s3_path)
    obj = s3_object.get()["Body"].read()
    raw_panel = pl.read_excel(
        io.BytesIO(obj),
        # Ignore infer datatype to float as it is not supported by xlsx2csv
        xlsx2csv_options={"ignore_formats": "float"},
        read_csv_options={"infer_schema_length": None},
    )
    return raw_panel.lazy()


@task
def load_batch_raw_panel(
    s3_bucket: str, s3_dir: str, time_col: str, entity_cols: List[str]
) -> pl.LazyFrame:
    s3_client = boto3.client("s3")
    # Get mapping of the all the keys with their last modified date
    key_to_last_modified = {
        obj["Key"]: obj["LastModified"]
        for obj in s3_client.list_objects(Bucket=s3_bucket, Prefix=s3_dir)["Contents"]
    }
    # Get mapping date_uploaded to objects based on the list of keys
    date_to_objects = {
        date.strftime("%Y-%m-%d %H:%M:%S"): s3_client.get_object(
            Bucket=s3_bucket, Key=key
        )["Body"].read()
        for key, date in key_to_last_modified.items()
    }
    # Read all files and append 'upload_date' column
    raw_panels = [
        pl.read_excel(
            io.BytesIO(obj),
            xlsx2csv_options={"ignore_formats": "float"},
            read_csv_options={"infer_schema_length": None},
        ).with_column(pl.lit(date).alias("upload_date"))
        for date, obj in date_to_objects.items()
    ]
    # Concat and drop duplicates based on time_col and entity_cols
    raw_panel = pl.concat(raw_panels).unique(
        subset=[time_col, *entity_cols], keep="last"
    )
    return raw_panel.lazy()


@task
def load_fct_panel(s3_bucket: str, s3_path: str):
    s3_client = boto3.resource("s3")
    s3_object = s3_client.Object(s3_bucket, s3_path)
    obj = s3_object.get()["Body"].read()
    fct_panel = pl.read_parquet(io.BytesIO(obj))
    return fct_panel


@task
def select_rows(df: pl.LazyFrame, filters: Mapping[str, List[str]]):
    for col, values in filters.items():
        filtered_df = df.filter(~pl.col(col).is_in(values))
    return filtered_df.collect(streaming=True).lazy()


@task
def clean_raw_panel(
    df: pl.LazyFrame,
    time_col: str,
    entity_cols: List[str],
) -> pl.LazyFrame:

    # Infer datetime format by using the first value
    fmt = infer_dt_format(str(df.collect().select([time_col])[0, 0]))
    new_col_names = {time_col: "time"}
    df_new = (
        df.rename(new_col_names)
        .with_columns(
            [
                # Parse datatime
                (pl.col("time").cast(pl.Utf8).str.strptime(pl.Date, fmt=fmt)),
                # Cast all float cols to int
                pl.col(pl.Float32).cast(pl.Int32),
                pl.col(pl.Float64).cast(pl.Int64),
                # Defensive replace #N/A generated by nulls/blanks to 0
                pl.col(entity_cols).str.replace("#N/A", "0"),
            ]
        )
        # Downcast numeric dtypes
        .select(pl.all().shrink_dtype())
        # Sort by entity and time
        .sort(by=[*entity_cols, "time"])
        .collect(streaming=True)
    )
    return df_new.lazy()


@task
def add_entity_effects(
    df: pl.LazyFrame, level_cols: List[str], dummy_entity_cols: List[str]
) -> pl.LazyFrame:
    expanded_entity = (
        df.collect()
        .select("entity")
        .with_columns(
            [
                pl.col("entity")
                .cast(pl.Utf8)
                .str.split(":")
                .arr.get(i)
                .alias(entity_col)
                for i, entity_col in enumerate(level_cols)
            ]
        )
    )
    fixed_effects = pl.get_dummies(expanded_entity.select(dummy_entity_cols)).select(
        pl.all().cast(pl.Boolean).prefix("is_")
    )
    # Replace spaces and semicolons with underscores
    fixed_effects.columns = [
        re.sub(r"[\s:]", "_", str(col).lower()) for col in fixed_effects.columns
    ]
    df_new = pl.concat([df.collect(), fixed_effects], how="horizontal")
    return df_new.lazy()


@task
def export_fct_panel(
    df: pl.LazyFrame, s3_bucket: str, raw_data_path: str, suffix: Optional[str] = None
):
    # Use the first 7 characters of the hash of raw data path as ID
    identifer = md5(raw_data_path.encode("utf-8")).hexdigest()[:7]
    ts = int(datetime.now().timestamp())
    s3_path = f"processed/{identifer}/{ts}"
    if suffix:
        s3_path = f"{s3_path}_{suffix}"
    df.collect().to_pandas().to_parquet(
        f"s3://{s3_bucket}/{s3_path}.parquet", index=False
    )
    return f"{s3_path}.parquet"


@flow
def preprocess_panel(inputs: PreprocessPanelInput) -> PreprocessPanelOutput:
    try:

        if inputs.raw_data_path.endswith(".xlsx"):
            raw_panel = load_raw_panel(inputs.s3_bucket, inputs.raw_data_path)
        else:
            raw_panel = load_batch_raw_panel(
                inputs.s3_bucket,
                inputs.raw_data_path,
                inputs.time_col,
                inputs.entity_cols,
            )
        raw_panel = (
            select_rows(raw_panel, inputs.filters)
            if inputs.filters is not None
            else raw_panel
        )
        fct_panel = clean_raw_panel(
            df=raw_panel,
            time_col=inputs.time_col,
            entity_cols=inputs.entity_cols,
        )
        paths = {
            "actual": export_fct_panel(
                fct_panel, inputs.s3_bucket, inputs.raw_data_path
            )
        }

        if inputs.manual_forecast_path is not None:
            if inputs.manual_forecast_path.endswith(".xlsx"):
                manual_forecasts = load_raw_panel(
                    inputs.s3_bucket, inputs.manual_forecast_path
                )
            else:
                manual_forecasts = load_batch_raw_panel(
                    inputs.s3_bucket,
                    inputs.manual_forecast_path,
                    inputs.time_col,
                    inputs.entity_cols,
                )
            manual_forecasts = (
                select_rows(manual_forecasts, inputs.filters)
                if inputs.filters is not None
                else manual_forecasts
            )
            fct_manual_forecast = clean_raw_panel(
                df=manual_forecasts,
                time_col=inputs.time_col,
                entity_cols=inputs.entity_cols,
            )
            paths["manual"] = export_fct_panel(
                fct_manual_forecast,
                inputs.s3_bucket,
                inputs.raw_data_path,
                suffix="manual",
            )

        start_date = fct_panel.collect().select(pl.min("time"))[0, 0]
        end_date = fct_panel.collect().select(pl.max("time"))[0, 0]

        paths["metadata"] = {
            "source_id": inputs.source_id,
            "freq": inputs.freq,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "status": "SUCCESS",
        }

    except Exception as exc:
        paths = {
            "metadata": {
                "source_id": inputs.source_id,
                "freq": inputs.freq,
                "status": "FAILED",
                "msg": str(repr(exc)),
            }
        }
    return paths


@task
def groupby_aggregate(
    df: pl.DataFrame,
    level_cols: List[str],
    target_col: str,
    agg_by: str,
    freq: str,
) -> pl.DataFrame:
    entity_id = ":".join(level_cols)
    agg_methods = {
        "sum": pl.sum(target_col),
        "mean": pl.mean(target_col),
    }

    df_new = (
        # Assign new col with entity_id
        df.with_column(pl.concat_str(level_cols, sep=":").alias(entity_id))
        .sort("time")
        .groupby(["time", entity_id], maintain_order=True)
        .agg(agg_methods[agg_by])
        # Defensive reorder columns
        .select([entity_id, "time", target_col])
        # Defensive resampling
        .groupby_dynamic("time", every=freq, by=entity_id)
        .agg(agg_methods[agg_by])
        # Defensive cast datetime col to pl.Datetime
        .with_column(pl.col("time").cast(pl.Datetime))
    )
    return df_new


@task
def filter_negative_values(
    df: pl.DataFrame,
    target_col: str,
) -> pl.DataFrame:

    df_new = df.with_column(
        # Remove negative values from target col
        pl.when(pl.col(target_col) <= 0)
        .then(0)
        .otherwise(pl.col(target_col))
        .keep_name()
    )
    return df_new


@task
def coerce_entity_colname(df: pl.LazyFrame, level_cols: List[str]) -> pl.LazyFrame:
    entity_id = ":".join(level_cols)

    # Coerce entity column name and defensive sort columns
    df_new = df.select(
        [
            # Coerce entity column name
            pl.col(entity_id).alias("entity"),
            pl.col("time"),
            # Include target col with prefix "target"
            pl.col("^target_.*$"),
            # Drop original entity_id col
            pl.all().exclude(["time", entity_id]),
        ]
    )
    return df_new


@task
def export_ftr_panel(
    df: pl.LazyFrame, s3_bucket: str, fct_data_path: str, suffix: Optional[str] = None
):
    # Use hash of fct data path and entity col as ID
    dataset_id = fct_data_path + df.columns[0]
    identifer = md5(dataset_id.encode("utf-8")).hexdigest()[:7]
    ts = int(datetime.now().timestamp())
    s3_path = f"processed/{identifer}/{ts}"
    if suffix:
        s3_path = f"{s3_path}_{suffix}"
    df.collect().to_pandas().to_parquet(
        f"s3://{s3_bucket}/{s3_path}.parquet", index=False
    )
    return f"{s3_path}.parquet"


@flow
def prepare_hierarchical_panel(
    inputs: PrepareHierarchicalPanelInput,
) -> PrepareHierarchicalPanelOutput:
    fct_panel = load_fct_panel(inputs.s3_bucket, inputs.fct_panel_path)
    ftr_panel = (
        filter_negative_values(fct_panel, inputs.target_col)
        if inputs.allow_negatives is False
        else fct_panel
    )
    ftr_panel = (
        groupby_aggregate(
            ftr_panel,
            inputs.level_cols,
            inputs.target_col,
            inputs.agg_method,
            inputs.freq,
        )
        .pipe(reindex_panel(freq=inputs.freq, sort=True))
        .rename({inputs.target_col: "target:actual"})
        .fill_null(0)
        .pipe(add_weekend_effects)
        .pipe(add_calendar_effects(attrs=DATE_FEATURES[inputs.freq]))
        .pipe(coerce_entity_colname, inputs.level_cols)
    )
    if inputs.dummy_entity_cols:
        ftr_panel = ftr_panel.pipe(
            add_entity_effects, inputs.level_cols, inputs.dummy_entity_cols
        )
    if inputs.country_codes:
        ftr_panel = ftr_panel.pipe(
            add_holiday_effects(inputs.country_codes, as_bool=True)
        )

    # zero inflated model does not accept boolean cols
    # pyarrow.lib.ArrowInvalid: Zero copy conversions not possible with boolean types
    ftr_panel = ftr_panel.pipe(transform_boolean_to_int)

    paths = {
        "actual": export_ftr_panel(ftr_panel, inputs.s3_bucket, inputs.fct_panel_path)
    }
    if inputs.manual_forecasts_path is None:
        with pl.StringCache():
            # Get length of time periods by entity
            y_len = (
                ftr_panel.groupby("entity")
                .agg(pl.count())
                .collect()
                .get_column("count")[0]
            )
            # Backtest period = length of time periods - minimum train size
            # n_splits = backtest period / test size
            n_splits = (y_len - MIN_TRAIN_SIZE[inputs.freq]) // TEST_SIZE[inputs.freq]

            n_split_to_ftr_train, n_split_to_ftr_test = get_train_test_splits(
                ftr_panel, n_splits, inputs.freq
            )

            backtests_by_model = []
            for model in BENCHMARK_MODELS:
                fit_kwargs = {
                    "freq": inputs.freq,
                    "lags": inputs.lags,
                    **MODEL_TO_SETTINGS[model],
                }

                backtest = (
                    run_backtest(
                        n_split_to_ftr_train=n_split_to_ftr_train,
                        n_split_to_ftr_test=n_split_to_ftr_test,
                        fit_kwargs=fit_kwargs,
                        quantile=None,
                    )
                    .with_column(pl.lit(model).alias("model"))
                    .select(["entity", "time", "model", "target:actual"])
                )
                backtests_by_model.append(backtest)

            postproc_kwargs = {
                "allow_negatives": inputs.allow_negatives,
                "use_manual_zeros": False,
            }

            transf_backtests_by_model = (
                postproc(y_preds=backtests_by_model,  ftr_panel_manual=None, ignore_zeros=False, **postproc_kwargs
                )
            )

            # Compute metrics and select the worse model
            if len(BENCHMARK_MODELS) > 1:
                metrics_by_model = []
                for model in BENCHMARK_MODELS:
                    backtest = (
                        transf_backtests_by_model
                        .filter(pl.col("model")==model)
                        .drop("model")
                    )
                    metrics = (
                        compute_metrics(
                            ftr_panel=ftr_panel,
                            ftr_panel_manual=backtest,
                            backtest=backtest,
                            quantile=None,
                        )
                        .drop("quantile")
                        .with_column(pl.lit(model).alias("model"))
                    )
                    metrics_by_model.append(metrics)
                metrics_by_model = pl.concat(metrics_by_model)

                benchmark_model = (
                    metrics_by_model
                    .groupby("model", maintain_order=True)
                    .agg([pl.col("mae:forecast").sum().round(2).keep_name()])
                    # Select the highest mae (worst model)
                    .sort("mae:forecast", reverse=True)
                    .collect()
                    .get_column("model")[0]
                )
            else:
                benchmark_model = BENCHMARK_MODELS[0]

            backtest = (
                transf_backtests_by_model
                .filter(pl.col("model")==model)
                .drop("model")
            )

            fit_kwargs = {
                "freq": inputs.freq,
                "lags": inputs.lags,
                **MODEL_TO_SETTINGS[benchmark_model],
            }
            y_pred = (
                run_forecast(
                    ftr_panel=ftr_panel, fit_kwargs=fit_kwargs, quantile=None
                )
                .pipe(lambda df: postproc(y_preds=[df], ftr_panel_manual=None, ignore_zeros=False, **postproc_kwargs)
                )
            )
            ftr_manual_forecast = pl.concat([backtest, y_pred]).pipe(
                lambda df: df.rename({df.columns[-1]: "target:manual"})
            )
            paths["manual_model"] = benchmark_model
    else:
        fct_manual_forecast = load_fct_panel(
            inputs.s3_bucket, inputs.manual_forecasts_path
        )
        ftr_manual_forecast = (
            filter_negative_values(fct_manual_forecast, inputs.target_col)
            if inputs.allow_negatives is False
            else fct_manual_forecast
        )
        ftr_manual_forecast = (
            groupby_aggregate(
                ftr_manual_forecast,
                inputs.level_cols,
                inputs.target_col,
                inputs.agg_method,
                inputs.freq,
            )
            .pipe(reindex_panel(freq=inputs.freq, sort=True))
            .fill_null(0)
            .rename({inputs.target_col: "target:manual"})
            .pipe(coerce_entity_colname, inputs.level_cols)
        )
        paths["manual_model"] = "manual"
    paths["manual"] = export_ftr_panel(
        ftr_manual_forecast, inputs.s3_bucket, inputs.fct_panel_path, suffix="manual"
    )

    return paths
