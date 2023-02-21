import io
import itertools
from datetime import datetime
from dateutil.relativedelta import relativedelta
from hashlib import md5
from typing import Any, List, Mapping, Optional, Tuple

import boto3
import joblib
import pandas as pd
import polars as pl
from lightgbm import LGBMRegressor
from prefect import flow, task
from pydantic import BaseModel, validator
from sklearn.linear_model import QuantileRegressor

from functime.cross_validation import select_splits, expanding_window_split
from functime.feature_extraction import (
    add_calendar_effects,
    add_holiday_effects
)
from functime.metrics import mae, overforecast, underforecast, smape
from functime.forecasting import zero_inflated_model, knn, lightgbm, snaive
from lightgbm import LGBMRegressor, LGBMClassifier

NUM_THREADS = joblib.cpu_count()
DATE_FEATURES = {
    "1d": ["day", "week", "weekday", "month"],
    "1mo": ["month", "year"],
    "3mo": ["quarter", "year"],
    "1y": ["year"],
}
PRED_FH = {"3mo": 3, "1mo": 8, "1w": 12, "1d": 21}
BACKTEST_FH = {"3mo": 9, "1mo": 12, "1w": 18, "1d": 30}
TEST_SIZE = {"3mo": 3, "1mo": 4, "1w": 6, "1d": 10}
# For quarter and monthly freq, takes from previous year
# For weekly and daily freq, takes from previous month
X_LAG = {"3mo": relativedelta(years=1), "1mo": relativedelta(years=1), "1w": relativedelta(months=1), "1d": relativedelta(months=1)}
SP = {"3mo": 4, "1mo": 12, "1w": 52, "1d": 30}
N_SPLITS = 3
QUANTILES = [
    0.1,
    0.15,
    0.2,
    0.25,
    0.3,
    0.35,
    0.4,
    0.45,
    0.5,
    0.55,
    0.6,
    0.65,
    0.7,
    0.75,
    0.8,
    0.85,
    0.9,
]

MODEL_TO_SETTINGS = {
    "zero_inflated:lgbm":{
        "use_zero_inflated": True,
        "regressor":LGBMRegressor(objective="quantile", alpha=0.5),
        "classifier":LGBMClassifier(objective="quantile", alpha=0.5),
        "model":None,
        "use_auto":False,
    },
    "zero_inflated:quantile_regressor":{
        "use_zero_inflated": True,
        "regressor":QuantileRegressor(solver="highs", alpha=0.5),
        "classifier":LGBMClassifier(objective="quantile", alpha=0.5),
        "model":None,
        "use_auto":False,
    },
    "knn":{
        "use_zero_inflated": False,
        "regressor":None,
        "classifier":None,
        "model":knn,
        "use_auto":False,
    },
    "snaive":{
        "use_zero_inflated": False,
        "regressor":None,
        "classifier":None,
        "model":snaive,
        "use_auto":False,
    },
    "lightgbm":{
        "use_zero_inflated": False,
        "regressor":None,
        "classifier":None,
        "model":lightgbm,
        "use_auto":False,
    },
}

ENSEMBLE_TO_MODELS = {
    "zero_inflated:lgbm+zero_inflated:quantile_regressor":["zero_inflated:lgbm", "zero_inflated:quantile_regressor"],
	"zero_inflated:lgbm+knn":["zero_inflated:lgbm","knn"],
    "zero_inflated:lgbm+knn+zero_inflated:quantile_regressor":["zero_inflated:lgbm","knn", "zero_inflated:quantile_regressor"],
	"zero_inflated:lgbm+snaive":["zero_inflated:lgbm","snaive"],
    "zero_inflated:lgbm+snaive+zero_inflated:quantile_regressor":["zero_inflated:lgbm", "snaive", "zero_inflated:quantile_regressor"],
	"zero_inflated:lgbm+knn+snaive":["zero_inflated:lgbm", "knn", "snaive"],
    "zero_inflated:lgbm+knn+snaive+zero_inflated:quantile_regressor":["zero_inflated:lgbm", "knn" ,"snaive", "zero_inflated:quantile_regressor"],
}

# Select columns from X if column = feature_cols
FEATURES_TO_COLS = {
    "add_weekend":{
        "feature_cols":["is_weekend"],
        "add_dummy_entity":False,
        "add_holiday": False,
        "append": True,
    },
    "add_calendar":{
        "feature_cols":["day", "weekday", "week", "month", "quarter", "year"],
        "add_dummy_entity":False,
        "add_holiday": False,
        "append": True,
    },
    "add_holiday":{
        "feature_cols":[],
        "add_dummy_entity":False,
        "add_holiday": True,
        "append": True,
    },
    "add_dummies":{
        "feature_cols":[],
        "add_dummy_entity":True,
        "add_holiday": False,
        "append": True,
    },
}


class RunForecastFlowInput(BaseModel):
    s3_data_bucket: str
    s3_artifacts_bucket: str
    ftr_data_paths: Mapping[str, str]
    s3_tscatalog_bucket: str = None
    external_data_paths: Optional[List[str]] = None
    freq: str
    lags: List[int]
    dummy_entity_cols: Optional[List[str]] = None
    allow_negatives: bool = False
    use_manual_zeros: bool = False

    @validator("freq")
    def check_freq(cls, freq):
        if freq not in PRED_FH:
            raise ValueError(f"Frequency `{freq}` is not supported.")
        return freq


class RunForecastFlowOutput(BaseModel):
    backtests: str
    metrics: str
    y_preds: str
    feature_importances: str


@task
def load_ftr_panel(s3_bucket: str, s3_path: str) -> pl.LazyFrame:
    s3_client = boto3.resource("s3")
    s3_object = s3_client.Object(s3_bucket, s3_path)
    obj = s3_object.get()["Body"].read()
    ftr_panel = pl.read_parquet(io.BytesIO(obj))
    return ftr_panel.lazy()


@task
def load_external_data(s3_bucket: str, s3_path: str) -> pl.LazyFrame:
    # s3_client = boto3.resource("s3")
    # s3_object = s3_client.Object(s3_bucket, s3_path)
    # obj = s3_object.get()["Body"].read()
    # external_data = pl.read_parquet(io.BytesIO(obj))
    external_data = pl.read_parquet(s3_path)
    return external_data.lazy()


@task
def join_external_data(ftr_panel: pl.LazyFrame, X: pl.LazyFrame, freq:str) -> pl.LazyFrame:
    idx_cols = ftr_panel.columns[:2]
    dtypes = ftr_panel.select(idx_cols).dtypes

    # Create new index for external data using timestamps and entities
    entities = ftr_panel.collect().get_column("entity").unique()
    dates = X.collect().get_column("time").unique()
    full_idx = pl.DataFrame(
        itertools.product(entities, dates), columns=idx_cols
    ).lazy()

    # Defensive cast dtypes to be consistent with df
    full_idx = full_idx.select(
        [pl.col(col).cast(dtypes[i]) for i, col in enumerate(full_idx.columns)]
    )

    X_new = (
        # Reindex external data
        X.join(full_idx, on="time", how="outer")
        # Resampling
        .groupby_dynamic("time", every=freq, by="entity")
        .agg(
            [
                pl.sum(col) 
                for col in X.columns 
                if col not in ["entity", "time"]
            ]
        )
    )
    
    joined_ftr_panel = (
        # Join with ftr_panel
        ftr_panel.join(X_new, on=idx_cols, how="left")
        # Fill nulls with 0
        .fill_null(0)
    )
    return joined_ftr_panel


def add_weekend_effects(df: pl.LazyFrame) -> pl.LazyFrame:
    exprs = [
        pl.col("time").dt.weekday().is_in([6, 7]).cast(pl.Int32).alias("is_weekend"),
    ]
    df_new = df.with_columns(exprs)
    return df_new


def transform_boolean_to_int(df: pl.LazyFrame) -> pl.LazyFrame:
    cols = df.select(pl.col(pl.Boolean())).columns
    df_new = df.with_columns(
        [
            pl.when(pl.col(col)==True).then(1).otherwise(0).keep_name()
            for col in cols
        ]
    )
    return df_new


@task
def get_train_test_splits(
    ftr_panel: pl.LazyFrame, n_splits: int, freq: str
) -> Mapping[int, pl.LazyFrame]:
    n_split_to_ftr_train = {}
    n_split_to_ftr_test = {}
    cv = expanding_window_split(TEST_SIZE[freq], n_splits=n_splits, step_size=TEST_SIZE[freq])
    splits = cv(ftr_panel)

    for i in range(n_splits):
        cols = {col:col.replace(f"_{i}", "") for col in splits.columns if col.endswith(str(i))}
        splits_i = splits.select(["entity", *list(cols.keys())]).rename(cols)
        train, test = select_splits(splits_i)
        train_cols = [col for col in train.columns if col not in ["entity", "time:train"]]
        test_cols = [col for col in test.columns if col not in ["entity", "time:test"]]
        train_new_cols = {
            col: col.replace(":train", "")
            for col in train.columns
        }
        test_new_cols = {
            col: col.replace(":test", "")
            for col in test.columns
        }
        n_split_to_ftr_train[i] = train.select(["entity", "time:train", *train_cols]).rename(train_new_cols)
        n_split_to_ftr_test[i] = test.select(["entity", "time:test", *test_cols]).rename(test_new_cols)
    return n_split_to_ftr_train, n_split_to_ftr_test


def _fit_and_predict(
    y: pl.LazyFrame,
    X: pl.LazyFrame,
    X_future: pl.LazyFrame,
    freq: str,
    lags: List[int],
    use_zero_inflated: bool,
    regressor=None, # required if use_zero_inflated = True
    classifier=None, # required if use_zero_inflated = True
    model=None, # required if use_zero_inflated = False
    use_auto: bool = False, # required if model is not None
    fh: int = None
) -> pl.LazyFrame:
    kwargs = {}
    min_lags = lags[0]
    max_lags = lags[-1]
    dtypes = y.dtypes

    n_obs = y.collect().get_column("time").n_unique()
    if n_obs < max_lags:
        max_lags = int(n_obs / 2)

    if model is not None and model == knn:
        # Default is 5
        kwargs = {"n_neighbors":max_lags}
    
    if use_zero_inflated:
        y_pred = zero_inflated_model(
            lags=max_lags,
            regressor=regressor,
            classifier=classifier,
            n_models=fh
        )(y=y, X=X, X_future=X_future, fh=fh, freq=freq)
    else:
        if model == snaive:
            forecaster = model(sp=SP[freq], fh=fh, **kwargs)
            y_pred = (
                forecaster
                .fit(y=y)
                .predict(fh=fh, freq=freq)
            )
        else:
            if use_auto:
                forecaster = model(min_lags=min_lags, max_lags=max_lags, n_models=fh, **kwargs)
            else:
                forecaster = model(lags=max_lags, n_models=fh, **kwargs)
            y_pred = (
                forecaster
                .fit(y=y, X=X)
                .predict(fh=fh, freq=freq, X=X_future)
            )

    # Defensive cast
    y_pred = (
        y_pred
        .with_columns(
            [
                pl.col(col).cast(dtypes[i])
                for i, col in enumerate(y_pred.columns)
                if col != "threshold_proba"
            ]
        )
    )
    
    return y_pred.lazy()


def _split_y_and_X(ftr_panel: pl.LazyFrame, feature_cols: List[str] = None) -> Tuple[pl.LazyFrame, pl.LazyFrame]:
    cols = ["entity", "time", "target:actual"]
    y = ftr_panel.select(cols)
    X = ftr_panel.select(["entity", "time", pl.all().exclude(cols)])

    if feature_cols is not None:
        X = X.select(["entity", "time", *feature_cols])
    return y, X


def _get_X_future(X: pl.LazyFrame, freq: str, fh: int) -> pl.LazyFrame:
    idx_cols = ["entity", "time"]
    dtypes = X.select(idx_cols).dtypes
    entities = X.collect().get_column("entity").unique()
    dates = X.collect().get_column("time")
    # Start date = original start date + lag
    start_date = dates.min() + X_LAG[freq]
    max_date = dates.max()
    # Get unique dates count
    period = dates.n_unique() - 1
    # TODO: need to refactor
    if freq == "3mo":
        # End date = start date + (unique dates count * 3 months)
        end_date = start_date + relativedelta(months=period * 3)
        # Future start date = end date + 3 months
        future_start_date = max_date + relativedelta(months=3)
        # Future end date = future start date + (fh * 3 months)
        future_end_date = future_start_date + relativedelta(months=(fh-1)* 3)
    elif freq == "1mo":
        # End date = start date + unique dates count
        end_date = start_date + relativedelta(months=period)
        # Future start date = end date + 1 month
        future_start_date = max_date + relativedelta(months=1)
        # Future end date = future start date + fh
        future_end_date = future_start_date + relativedelta(months=fh-1)
    elif freq == "1w":
        # End date = start date + unique dates count
        end_date = start_date + relativedelta(weeks=period)
        # Future start date = end date + 1 week
        future_start_date = max_date + relativedelta(weeks=1)
        # Future end date = future start date + fh
        future_end_date = future_start_date + relativedelta(weeks=fh-1)
    else:
        # End date = start date + unique dates count
        end_date = start_date + relativedelta(days=period)
        # Future start date = end date + 1 day
        future_start_date = max_date + relativedelta(days=1)
        # Future end date = future start date + fh
        future_end_date = future_start_date + relativedelta(days=fh-1)
    # Lagged dates
    timestamps = pl.date_range(start_date, end_date, interval=freq)
    # Create new idx df using lagged dates + entities
    full_idx = pl.DataFrame(
            itertools.product(entities, timestamps), columns=idx_cols
        )
    # Defensive cast dtypes to be consistent with df
    full_idx = full_idx.select(
        [pl.col(col).cast(dtypes[i]) for i, col in enumerate(full_idx.columns)]
    )

    # Drop calendar features, is weekend, and holidays
    drop_cols = [col for col in X.columns if col in ["is_weekend"] + [value for values in DATE_FEATURES.values() for value in values] or col.startswith("holidays:")]

    # Select entity, time from new idx then concat with X (all columns excludes entity, time)
    X_future = (
        pl.concat([full_idx.sort(idx_cols), X.sort(idx_cols).select(pl.all().exclude(idx_cols + drop_cols)).collect()], how="horizontal")
        .lazy()
        # Slice by fh dates
        .filter(pl.col("time").is_between(future_start_date, future_end_date, include_bounds=True))
        # Defensive cast datetime col to pl.Datetime
        .with_column(pl.col("time").cast(pl.Datetime))
        # Re-generate calendar features, is weekend, and holidays 
        .pipe(add_weekend_effects)
        .pipe(add_calendar_effects(attrs=DATE_FEATURES[freq]))
    )

    country_codes = [col.replace("holidays:","") for col in X.columns if col.startswith("holidays:")]
    if len(country_codes)>0:
        X_future = X_future.pipe(
            add_holiday_effects(country_codes, as_bool=True)
        )

    X_future = X_future.pipe(transform_boolean_to_int)
    return X_future


@task
def run_backtest(
    n_split_to_ftr_train: Mapping[int, pl.LazyFrame],
    n_split_to_ftr_test: Mapping[int, pl.LazyFrame],
    fit_kwargs: Mapping[str, Any],
    quantile: float = None,
) -> pl.LazyFrame:
    # Unpack fit_kwargs
    freq = fit_kwargs["freq"]
    y_preds = []

    # TODO: Need to refactor
    if quantile is not None:
        use_zero_inflated = fit_kwargs["use_zero_inflated"]
        if use_zero_inflated:
            regressor = fit_kwargs["regressor"]
            if isinstance(regressor, LGBMRegressor):
                fit_kwargs["regressor"] = LGBMRegressor(objective="quantile", alpha=quantile)
            elif isinstance(regressor, QuantileRegressor):
                fit_kwargs["regressor"] = QuantileRegressor(solver="highs", alpha=quantile)

            fit_kwargs["classifier"] = LGBMClassifier(objective="quantile", alpha=quantile)

    for n_split, ftr_train in n_split_to_ftr_train.items():
        ftr_test = n_split_to_ftr_test[n_split]
        y, X = _split_y_and_X(ftr_train)
        _, X_future = _split_y_and_X(ftr_test)
        y_pred = _fit_and_predict(
            y=y, 
            X=X,
            X_future=X_future,
            fh=TEST_SIZE[freq],
            **fit_kwargs,
        )

        y_preds.append(y_pred)

    y_preds = pl.concat(y_preds)
    if quantile is not None:
        y_preds = y_preds.with_column(pl.lit(quantile).alias("quantile"))

    if "threshold_proba" in y_preds.columns:
        y_preds = y_preds.select(pl.all().exclude("threshold_proba"))
    
    return y_preds #, fitted_model


def _run_ensemble(
    y_pred: pl.LazyFrame,
    idx_cols: List[str],
    ignore_zeros: bool, # Ignore zeros when averaging forecast columns
) -> pl.LazyFrame:
    target_cols = [col for col in y_pred.columns if col.startswith("target")]
    # Get the dtype
    target_dtype = y_pred.select(target_cols).dtypes[0]
    y_pred_mean = y_pred.select(pl.all().exclude(idx_cols))

    if ignore_zeros:
        # Convert zero to None
        y_pred_mean = y_pred_mean.with_columns(
            [
                pl.when(pl.col(col)==0)
                .then(None)
                .otherwise(pl.col(col))
                for col in y_pred_mean.columns
            ]
        )

    y_pred_mean = (
        y_pred_mean.collect()
        .mean(axis=1)
        # Cast target column to actual dtype
        .cast(target_dtype)
        .fill_null(0)
        .alias("target:actual")
    )

    transf_y_pred = y_pred.select([pl.col(idx_cols), y_pred_mean])
    return transf_y_pred.lazy()


@task
def postproc(
    y_preds: List[pl.LazyFrame],
    ftr_panel_manual: pl.LazyFrame,
    allow_negatives: bool,
    use_manual_zeros: bool,
    ignore_zeros: bool, # Ignore zeros when averaging forecast columns
) -> pl.LazyFrame:
    y_pred = pl.concat(y_preds)
    idx_cols = [col for col in y_pred.columns if col in ["model", "entity", "time", "quantile"]]

    y_pred = (
        # Ensemble if there are multiple forecast columns
        _run_ensemble(y_pred, idx_cols, ignore_zeros)
        .rename({"target:actual":"target:forecast"})
    )

    if use_manual_zeros:
        # Replace forecast to 0 according to manual forecast
        y_pred = (
            y_pred.join(ftr_panel_manual, on=["entity", "time"], how="left")
            .with_column(
                pl.when(pl.col("target:manual") <= 0)
                .then(0)
                .otherwise(pl.col("target:forecast"))
                .alias("target:forecast")
            )
            .select(
                pl.col(
                    [
                        *idx_cols,
                        "target:forecast",
                    ]
                )
            )
        )

    if not allow_negatives:
        # Replace negative forecast to 0
        y_pred = y_pred.with_column(
            pl.when(pl.col("target:forecast") < 0)
            .then(0)
            .otherwise(pl.col("target:forecast"))
            .alias("target:forecast")
        )
    return y_pred


@task
def compute_metrics(
    ftr_panel: pl.LazyFrame,
    ftr_panel_manual: pl.LazyFrame,
    backtest: pl.LazyFrame,
    quantile: float,
) -> pl.LazyFrame:
    # Get backtest dates
    backtest_dates = (
        backtest.select(pl.col("time").unique()).collect().get_column("time").to_list()
    )
    # Drop additional features
    ftr_panel = ftr_panel.select(["entity", "time", "target:actual"])
    # Drop quantile column
    backtest = backtest.select(["entity", "time", "target:forecast"])

    forecast_mae = mae(y_true=ftr_panel, y_pred=backtest)
    forecast_underforecast = underforecast(y_true=ftr_panel, y_pred=backtest)
    forecast_overforecast = overforecast(y_true=ftr_panel, y_pred=backtest)
    forecast_smape = smape(y_true=ftr_panel, y_pred=backtest)

    # Add manual mae, underforecast, overforecsat, smape, rank, and improvement columns
    # Filter manual forecast by backtest dates
    ftr_panel_manual = ftr_panel_manual.filter(pl.col("time").is_in(backtest_dates))
    manual_mae = mae(y_true=ftr_panel, y_pred=ftr_panel_manual)
    manual_underforecast = underforecast(y_true=ftr_panel, y_pred=ftr_panel_manual)
    manual_overforecast = overforecast(y_true=ftr_panel, y_pred=ftr_panel_manual)
    manual_smape = smape(y_true=ftr_panel, y_pred=ftr_panel_manual)

    merged_mae = (
        manual_mae.join(forecast_mae, on="entity", how="outer", suffix=":forecast").rename({"mae":"mae:manual"})
        .with_column(

            (pl.col("mae:manual") - pl.col("mae:forecast")).alias(
                "mae_improvement"
            )
        )
        .with_columns(
            [
                (pl.col("mae_improvement") / pl.col("mae:manual") * 100).alias(
                    "mae_improvement_%"
                ),
                pl.col("mae:manual").rank(method="min").alias("mae_rank:manual"),
            ]
        )
    )
    merged_underforecast = (
        manual_underforecast
        .join(
        forecast_underforecast, on="entity", how="outer", suffix=":forecast"
        )
        .rename({"underforecast":"underforecast:manual"})
        .with_column(
            (pl.col("underforecast:manual") - pl.col("underforecast:forecast")).alias(
                "underforecast_improvement"
            )
        )
        .with_column(
            (pl.col("underforecast_improvement") / pl.col("underforecast:manual")
                * 100
            ).alias("underforecast_improvement_%")
        )
    )
    merged_overforecast = (
        manual_overforecast
        .join(
        forecast_overforecast, on="entity", how="outer", suffix=":forecast"
        )
        .rename({"overforecast":"overforecast:manual"})
        .with_column(
            (pl.col("overforecast:manual") - pl.col("overforecast:forecast")).alias(
                "overforecast_improvement"
            )
        )
        .with_column(
            (pl.col("overforecast_improvement") / pl.col("overforecast:manual")
                * 100
            ).alias("overforecast_improvement_%")
        )
    )
    merged_smape = (
        manual_smape.join(forecast_smape, on="entity", how="outer", suffix=":forecast").rename({"smape":"smape:manual"})
        .with_column(

            (pl.col("smape:manual") - pl.col("smape:forecast")).alias(
                "smape_improvement"
            )
        )
        .with_column(
            (pl.col("smape_improvement") / pl.col("smape:manual") * 100).alias(
                "smape_improvement_%"
            ),
        )
    )

    metrics = (
        merged_mae
        .join(merged_underforecast, on="entity", how="outer")
        .join(merged_overforecast, on="entity", how="outer")
        .join(merged_smape, on="entity", how="outer")
        .pipe(
        lambda df: df
            # Reorder columns sequence - index col, quantile, others
            .select(
                [
                    pl.col("entity"),
                    pl.lit(quantile).alias("quantile"),
                ]
                +
                # Replace inf/null/nan to 0
                [
                    pl.when(pl.col(col).cast(pl.Float64).is_infinite() | pl.col(col).is_null() | pl.col(col).cast(pl.Float64).is_nan())
                    .then(0)
                    .otherwise(pl.col(col))
                    .keep_name()
                    for col in df.columns
                    if col not in ["entity", "quantile"]
                ]
            )
        )
    )
    return metrics.lazy()


@task
def run_forecast(
    ftr_panel: pl.LazyFrame,
    fit_kwargs: Mapping[str, Any],
    quantile: float = None,
):
    # TODO: Need to refactor
    if quantile is not None:
        use_zero_inflated = fit_kwargs["use_zero_inflated"]
        if use_zero_inflated:
            regressor = fit_kwargs["regressor"]
            if isinstance(regressor, LGBMRegressor):
                fit_kwargs["regressor"] = LGBMRegressor(objective="quantile", alpha=quantile)
            elif isinstance(regressor, QuantileRegressor):
                fit_kwargs["regressor"] = QuantileRegressor(solver="highs", alpha=quantile)

            fit_kwargs["classifier"] = LGBMClassifier(objective="quantile", alpha=quantile)

    freq = fit_kwargs["freq"]
    y, X = _split_y_and_X(ftr_panel)
    X_future = _get_X_future(X, freq, PRED_FH[freq])
    y_pred = _fit_and_predict(
        y=y, 
        X=X,
        X_future=X_future,
        fh=PRED_FH[freq],
        **fit_kwargs,
    )

    if quantile is not None:
        y_pred = y_pred.with_column(pl.lit(quantile).alias("quantile"))

    return y_pred


@task
def compute_feature_importance(
    fitted_model_by_quantile: Mapping[int, Any], quantile: int
):
    try:
        # Find the first LGBMRegressor in the list of models
        fitted_model = next(
            model
            for model in fitted_model_by_quantile[quantile].models_
            if isinstance(model, LGBMRegressor)
        )
    except StopIteration as err:
        raise ValueError("Missing LGBMRegressor in `fitted_model`") from err

    feature_importance = pl.DataFrame(
        {
            "quantile": [quantile] * fitted_model.n_features_,
            "feature_name": fitted_model.feature_name_,
            "importance": fitted_model.feature_importances_.tolist(),
        }
    ).sort("importance", reverse=True)

    return feature_importance.lazy()


@task
def export_panel(
    df: pl.LazyFrame, s3_bucket: str, ftr_data_path: str, suffix: Optional[str] = None
):
    # Use hash of ftr data actual path as ID (first 7 char)
    identifer = md5(ftr_data_path.encode("utf-8")).hexdigest()[:7]
    ts = int(datetime.now().timestamp())
    s3_path = f"forecast/{identifer}/{ts}"
    if suffix:
        s3_path = f"{s3_path}/{suffix}"
    df.collect().to_pandas().to_parquet(
        f"s3://{s3_bucket}/{s3_path}.parquet", index=False
    )
    return f"{s3_path}.parquet"


@task
def get_feature_cols(
    ftr_panel: pl.LazyFrame,
    feature_cols,
    add_dummy_entity,
    dummy_entity_cols,
    add_holiday,
) -> List[str]:
    if add_dummy_entity and dummy_entity_cols:
        for dummy_entity_col in dummy_entity_cols:
            feature_cols = feature_cols + [col for col in ftr_panel.columns if col.startswith(f"is_{dummy_entity_col}") ]

    if add_holiday:
        feature_cols = feature_cols + [col for col in ftr_panel.columns if col.startswith("holidays:") ]

    feature_cols = [col for col in feature_cols if col in ftr_panel.columns]
    return feature_cols


@flow
def run_forecast_flow(inputs: RunForecastFlowInput) -> RunForecastFlowOutput:
    with pl.StringCache():
        freq = inputs.freq

        # 1. Load ftr tables
        ftr_panel = load_ftr_panel(
            s3_bucket=inputs.s3_data_bucket, s3_path=inputs.ftr_data_paths["actual"]
        )
        ftr_panel_manual = (
            load_ftr_panel(
                s3_bucket=inputs.s3_data_bucket, s3_path=inputs.ftr_data_paths["manual"]
            )
            # Defensive cast
            .with_column(
                pl.col("target:manual").cast(ftr_panel.select("target:actual").dtypes[0])
            )
        )

        # 2. Load external data and join with ftr_panel
        if inputs.external_data_paths:
            for external_data_path in inputs.external_data_paths:
                external_data = load_external_data(s3_bucket=inputs.s3_tscatalog_bucket, s3_path=external_data_path)
                ftr_panel = join_external_data(ftr_panel=ftr_panel, X=external_data, freq=freq)

        # 3. Get manual model
        manual_model = inputs.ftr_data_paths["manual_model"]

        # 4. Time series split - return mapping of n_split to LazyFrame
        splits_kwargs = {"freq": freq}
        n_split_to_ftr_train, n_split_to_ftr_test = get_train_test_splits(
            ftr_panel=ftr_panel, n_splits=N_SPLITS, **splits_kwargs
        )

        # 5. Train all individual models without external features - for uplift
        fit_kwargs = {
            "freq": freq,
            "lags": inputs.lags,
        }
        uplift_postproc_kwargs = {
            "allow_negatives": inputs.allow_negatives,
            "use_manual_zeros": False,
            "ftr_panel_manual": ftr_panel_manual,
        }
        backtests_by_model = []
        for model, settings in MODEL_TO_SETTINGS.items():
            # Skip if model = manual/benchmark model
            if model == manual_model:
                continue

            fit_kwargs_by_model = {
                **fit_kwargs,
                **settings
            }
            backtest_by_model = (
                run_backtest(
                    n_split_to_ftr_train=n_split_to_ftr_train,
                    n_split_to_ftr_test=n_split_to_ftr_test,
                    quantile=None,
                    fit_kwargs=fit_kwargs_by_model,
                )
                .with_column(pl.lit(model).alias("model"))
            )

            backtests_by_model.append(backtest_by_model)

        transf_backtests_by_model = (
            postproc(y_preds=backtests_by_model, ignore_zeros=False, **uplift_postproc_kwargs
            )
        )

        # 6. Ensemble models
        backtests_by_ensemble = []
        for ensemble, models in ENSEMBLE_TO_MODELS.items():
            # Skip if ensemble contains manual/benchmark model
            if manual_model in models:
                continue

            ensemble_backtest = None
            for model in models:
                backtest = (
                    transf_backtests_by_model
                    .filter(pl.col("model")==model)
                    .rename({"target:forecast":f"target:forecast:{model}"})
                    .drop("model")
                )

                if ensemble_backtest is None:
                    ensemble_backtest = backtest
                else:
                    ensemble_backtest = (
                        ensemble_backtest.join(backtest, on=["entity", "time"])
                    )
            transf_ensemble_backtest = (
                postproc(y_preds=[ensemble_backtest], ignore_zeros=False, **uplift_postproc_kwargs
                ).with_column(pl.lit(ensemble).alias("model"))
            )
            backtests_by_ensemble.append(transf_ensemble_backtest)
        backtests_by_ensemble = pl.concat(backtests_by_ensemble)

        paths = {
            "backtests_by_ensemble": export_panel(
                backtests_by_ensemble,
                inputs.s3_artifacts_bucket,
                inputs.ftr_data_paths["actual"],
                suffix="backtests_by_ensemble",
            )
        }

        # 7. Compute metrics for ensemble
        metrics_by_ensemble = []
        for ensemble, models in ENSEMBLE_TO_MODELS.items():
            # Skip if ensemble contains manual/benchmark model
            if manual_model in models:
                continue
            backtest = (
                backtests_by_ensemble
                .filter(pl.col("model")==ensemble)
                .drop("model")
            )
            metric = (
                compute_metrics(
                    ftr_panel=ftr_panel,
                    ftr_panel_manual=ftr_panel_manual,
                    backtest=backtest,
                    quantile=None,
                )
                .drop("quantile")
                .with_column(pl.lit(ensemble).alias("model"))
            )
            metrics_by_ensemble.append(metric)

        metrics_by_ensemble = pl.concat(metrics_by_ensemble)
        paths["metrics_by_ensemble"] = export_panel(
            metrics_by_ensemble,
            inputs.s3_artifacts_bucket,
            inputs.ftr_data_paths["actual"],
            suffix="metrics_by_ensemble",
        )

        # 8. Select best ensemble model by lowest sum of MAE
        best_ensemble_model = (
            metrics_by_ensemble
            .groupby("model")
            .agg(pl.col("mae:forecast").sum())
            .sort("mae:forecast")
            .collect()
            .get_column("model")[0]
        )
        paths["best_ensemble_model"] = best_ensemble_model

        # Add best ensemble into transf_backtests_by_model
        transf_backtests_by_model = (
            pl.concat(
                [
                    transf_backtests_by_model,
                    backtests_by_ensemble
                    .filter(pl.col("model")==best_ensemble_model)
                    .select(
                        [
                            pl.col("entity"),
                            pl.col("time"),
                            pl.lit("ensemble").alias("model"),
                            pl.col("target:forecast"),
                        ]
                    )
                ]
            )
        )

        # 9. Add features sequantially to ensemble
        ensemble_models = ENSEMBLE_TO_MODELS[best_ensemble_model]
        
        backtests_by_feature = []
        ensemble_backtests_by_feature = {}
        append_feature_cols = []
        for feature, feature_settings in FEATURES_TO_COLS.items():
            feature_cols = feature_settings["feature_cols"]
            add_dummy_entity = feature_settings["add_dummy_entity"]
            add_holiday = feature_settings["add_holiday"]
            
            feature_cols = get_feature_cols(ftr_panel ,feature_cols, add_dummy_entity, inputs.dummy_entity_cols, add_holiday)

            if len(feature_cols)>0:
                append_feature_cols = append_feature_cols + feature_cols
                ftr_panel_by_feature = ftr_panel.select(["entity", "time", "target:actual", *append_feature_cols])
            else:
                # Skip if feature cols are not exist in ftr_panel
                continue

            # Run train test split
            n_split_to_ftr_train_by_feature, n_split_to_ftr_test_by_feature = get_train_test_splits(
                ftr_panel=ftr_panel_by_feature, n_splits=N_SPLITS, **splits_kwargs
            )
            ensemble_backtest = None
            # Train individual models using different set of features 
            for model in ensemble_models:
                settings = MODEL_TO_SETTINGS[model]
                fit_kwargs_by_model = {
                    **fit_kwargs,
                    **settings
                }

                backtest = (
                    run_backtest(
                        n_split_to_ftr_train=n_split_to_ftr_train_by_feature,
                        n_split_to_ftr_test=n_split_to_ftr_test_by_feature,
                        quantile=None,
                        fit_kwargs=fit_kwargs_by_model,
                    )
                    .rename({"target:actual":f"target:actual:{model}"})
                )
                if ensemble_backtest is None:
                    ensemble_backtest = backtest
                else:
                    ensemble_backtest = (
                        ensemble_backtest.join(backtest, on=["entity", "time"])
                    )

            if ensemble_backtest is not None: 
                ensemble_backtests_by_feature[feature] = ensemble_backtest

        for feature, backtest in ensemble_backtests_by_feature.items():
            transf_ensemble_backtest = (
                postproc(y_preds=[backtest], ignore_zeros=False, **uplift_postproc_kwargs
                ).with_column(pl.lit(f"ensemble_{feature}").alias("model"))
                .select(["entity", "time", "model", "target:forecast"])
            )
            backtests_by_feature.append(transf_ensemble_backtest)

            # If last feature, add ensemble + manual
            if feature == list(ensemble_backtests_by_feature.keys())[-1]:
                manual_backtest = (
                    ftr_panel_manual
                    .with_column(pl.lit("manual").alias("model"))
                    .rename({"target:manual":"target:forecast"})
                    .select(["entity", "time", "model", "target:forecast"])
                    .filter(pl.col("time").is_in(
                        backtest
                        .collect()
                        .get_column("time")
                        .unique()
                    ))
                )
                transf_ensemble_backtest = (
                    postproc(y_preds=[
                        backtest.join(manual_backtest.select(pl.all().exclude("model")), on=["entity", "time"])
                        ], ignore_zeros=False, **uplift_postproc_kwargs
                    ).with_column(pl.lit(f"ensemble+manual").alias("model"))
                    .select(["entity", "time", "model", "target:forecast"])
                )
                backtests_by_feature.append(transf_ensemble_backtest)
        
        transf_backtests_by_model = (
            pl.concat(
                [
                    transf_backtests_by_model, 
                    pl.concat(backtests_by_feature),
                    # Add manual into backtests by model for uplift
                    manual_backtest
                ]
            )
        )

        # 10. Overrides zero
        postproc_kwargs = {
            "allow_negatives": inputs.allow_negatives,
            "use_manual_zeros": inputs.use_manual_zeros,
            "ftr_panel_manual": ftr_panel_manual,
        }
        if inputs.use_manual_zeros:
            ensemble_overrides_zero_backtest = (
                postproc(y_preds=[backtests_by_feature[-1], manual_backtest], ignore_zeros=False, **postproc_kwargs
                ).with_column(pl.lit(f"ensemble+manual+overrides_zero").alias("model"))
            )
            transf_backtests_by_model = (
                pl.concat(
                    [
                        transf_backtests_by_model, 
                        ensemble_overrides_zero_backtest,
                    ]
                )
            )

        # 11. Export backtests for uplift models
        paths["backtests_by_model"] = export_panel(
            transf_backtests_by_model,
            inputs.s3_artifacts_bucket,
            inputs.ftr_data_paths["actual"],
            suffix="backtests_by_model",
        )

        # 12. Compute metrics for uplift models
        metrics_by_model = []
        uplift_models = (
            transf_backtests_by_model
            .collect().get_column("model").unique()
        )
        for model in uplift_models:
            backtest = (
                transf_backtests_by_model
                .filter(pl.col("model")==model)
                .drop("model")
            )
            metric = (
                compute_metrics(
                    ftr_panel=ftr_panel,
                    ftr_panel_manual=ftr_panel_manual,
                    backtest=backtest,
                    quantile=None,
                )
                .drop("quantile")
                .with_column(pl.lit(model).alias("model"))
            )
            metrics_by_model.append(metric)

        metrics_by_model = pl.concat(metrics_by_model)
        paths["metrics_by_model"] = export_panel(
            metrics_by_model,
            inputs.s3_artifacts_bucket,
            inputs.ftr_data_paths["actual"],
            suffix="metrics_by_model",
        )

        # 13. Backtest - return backtest and fitted_model by quantile using best ensemble model + manual
        backtests = []
        ensemble_models = ENSEMBLE_TO_MODELS[best_ensemble_model]
        for quantile in QUANTILES:
            ensemble_backtest = None
            for model in ensemble_models:
                settings = MODEL_TO_SETTINGS[model]
                fit_kwargs_by_model = {
                    **fit_kwargs,
                    **settings
                }

                backtest = (
                    run_backtest(
                        n_split_to_ftr_train=n_split_to_ftr_train,
                        n_split_to_ftr_test=n_split_to_ftr_test,
                        quantile=quantile,
                        fit_kwargs=fit_kwargs_by_model,
                    ).rename({"target:actual":f"target:actual:{model}"})
                )
                if ensemble_backtest is None:
                    ensemble_backtest = backtest
                else:
                    ensemble_backtest = (
                        ensemble_backtest.join(backtest, on=["entity", "time", "quantile"])
                    )

            joined_ensemble_backtest = (
                ensemble_backtest.join(
                    manual_backtest.drop("model").with_column(pl.lit(quantile).alias("quantile")), on=["entity", "time", "quantile"])
            )
            transf_ensemble_backtest = (
                postproc(y_preds=[joined_ensemble_backtest], ignore_zeros=False, **uplift_postproc_kwargs
                )
            )
            backtests.append(transf_ensemble_backtest)
        backtests = pl.concat(backtests)

        # 14. If overrides zero, add new forecast column suffixed "overrides_zero"
        if inputs.use_manual_zeros:
            backtests_overrides_zero = (
                postproc(y_preds=[backtests], ignore_zeros=False, **postproc_kwargs
                ).rename({"target:forecast":"target:forecast_overrides_zero"})
            )
            backtests = backtests.join(
                backtests_overrides_zero, on=["entity", "time", "quantile"]
            )

        paths["backtests"] = export_panel(
            backtests,
            inputs.s3_artifacts_bucket,
            inputs.ftr_data_paths["actual"],
            suffix="backtests",
        )

        # 15. Compute backtest metrics by quantile
        metrics = []
        for quantile in QUANTILES:
            backtest_by_quantile = backtests.filter(pl.col("quantile") == quantile)
            metric = compute_metrics(
                ftr_panel=ftr_panel,
                ftr_panel_manual=ftr_panel_manual,
                backtest=backtest_by_quantile,
                quantile=quantile,
            )
            metrics.append(metric)

        metrics = pl.concat(metrics)
        paths["metrics"] = export_panel(
            metrics,
            inputs.s3_artifacts_bucket,
            inputs.ftr_data_paths["actual"],
            suffix="metrics",
        )

        # 16. Training final model on the full dataset and predict by quantile using best ensemble model + manual
        y_preds = []
        ensemble_models = ENSEMBLE_TO_MODELS[best_ensemble_model]
        for quantile in QUANTILES:
            ensemble_y_pred = None
            for model in ensemble_models:
                settings = MODEL_TO_SETTINGS[model]
                fit_kwargs_by_model = {
                    **fit_kwargs,
                    **settings
                }

                y_pred = (
                    run_forecast(
                        ftr_panel=ftr_panel,
                        quantile=quantile,
                        fit_kwargs=fit_kwargs_by_model,
                    ).rename({"target:actual":f"target:actual:{model}"})
                )
                if ensemble_y_pred is None:
                    ensemble_y_pred = y_pred
                else:
                    ensemble_y_pred = (
                        ensemble_y_pred.join(y_pred, on=["entity", "time", "quantile"])
                    )

            joined_ensemble_y_pred = (
                ensemble_y_pred.join(
                    ftr_panel_manual
                    .filter(pl.col("time").is_in(ensemble_y_pred.collect().get_column("time").unique()))
                    .with_column(pl.lit(quantile).alias("quantile")), on=["entity", "time", "quantile"])
            )
            transf_ensemble_y_pred = (
                postproc(y_preds=[joined_ensemble_y_pred], ignore_zeros=True, **uplift_postproc_kwargs
                )
            )
            y_preds.append(transf_ensemble_y_pred)
        y_preds = pl.concat(y_preds)

        # 17. If overrides zero, add new forecast column suffixed "overrides_zero"
        if inputs.use_manual_zeros:
            y_preds_overrides_zero = (
                postproc(y_preds=[y_preds], ignore_zeros=True, **postproc_kwargs
                ).rename({"target:forecast":"target:forecast_overrides_zero"})
            )
            y_preds = y_preds.join(
                y_preds_overrides_zero, on=["entity", "time", "quantile"]
            )

        paths["y_preds"] = export_panel(
            y_preds,
            inputs.s3_artifacts_bucket,
            inputs.ftr_data_paths["actual"],
            suffix="y_preds",
        )

        # 7. Compute feature importance
        # feature_importances = []
        # for quantile in QUANTILES:
        #     feature_importances_by_quantile = compute_feature_importance(
        #         fitted_model_by_quantile, quantile
        #     )
        #     feature_importances.append(feature_importances_by_quantile)
        # feature_importances = pl.concat(feature_importances)

        # paths["feature_importances"] = export_panel(
        #     feature_importances,
        #     inputs.s3_artifacts_bucket,
        #     inputs.ftr_data_paths["actual"],
        #     suffix="feature_importances",
        # )

    return paths
