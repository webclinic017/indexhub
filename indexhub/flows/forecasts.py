import io
from datetime import datetime
from hashlib import md5
from typing import Any, List, Mapping, Optional

import boto3
import joblib
import pandas as pd
import polars as pl
from lightgbm import LGBMRegressor
from mlforecast import MLForecast
from prefect import flow, task
from sklearn.linear_model import QuantileRegressor
from sklearn.model_selection import TimeSeriesSplit
from window_ops.expanding import expanding_mean
from window_ops.rolling import rolling_mean

from indexhub.metrics import mad, smape

NUM_THREADS = joblib.cpu_count()
PRED_FH = {"Q": 3, "MS": 8, "W": 12, "D": 21}
BACKTEST_FH = {"Q": 9, "MS": 12, "W": 18, "D": 30}
TEST_SIZE = {"Q": 3, "MS": 4, "W": 6, "D": 10}
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


@task
def load_ftr_panel(s3_bucket: str, s3_path: str) -> pl.LazyFrame:
    s3_client = boto3.resource("s3")
    s3_object = s3_client.Object(s3_bucket, s3_path)
    obj = s3_object.get()["Body"].read()
    ftr_panel = pl.read_parquet(io.BytesIO(obj))
    return ftr_panel.lazy()


@task
def get_train_test_splits(
    ftr_panel: pl.LazyFrame, time_col: str, merged_index_col: str, freq: str
) -> Mapping[int, pl.LazyFrame]:
    # Create a Pandas dataframe from the panel and group it by the merged_index_col
    df = ftr_panel.collect().to_pandas().groupby(merged_index_col)
    # Initialize dictionaries to store training and testing sets for each split
    n_split_to_ftr_train = {}
    n_split_to_ftr_test = {}
    # Loop through each group in the dataframe
    for entity, dataframe in df:
        # Initialize TimeSeriesSplit object with specified number of splits and test size
        tscv = TimeSeriesSplit(n_splits=N_SPLITS, test_size=TEST_SIZE[freq])
        # Get the train and test indices for each split
        for n_split, (train_idx, test_idx) in enumerate(
            tscv.split(dataframe.set_index(time_col))
        ):
            # Filter the panel to get the rows corresponding to the current entity
            filtered_ftr_panel = ftr_panel.filter(pl.col(merged_index_col) == entity)
            # Get the training and testing sets for the current split and entity
            ftr_train = filtered_ftr_panel.slice(
                offset=train_idx[0], length=len(train_idx)
            )
            ftr_test = filtered_ftr_panel.slice(
                offset=test_idx[0], length=len(test_idx)
            )
            # Append the training and testing sets to the dictionaries
            n_split_to_ftr_train.setdefault(n_split, []).append(ftr_train)
            n_split_to_ftr_test.setdefault(n_split, []).append(ftr_test)
    # Concatenate the training and testing sets for each split
    n_split_to_ftr_train = {
        n_split: pl.concat(ftr_trains)
        for n_split, ftr_trains in n_split_to_ftr_train.items()
    }
    n_split_to_ftr_test = {
        n_split: pl.concat(ftr_tests)
        for n_split, ftr_tests in n_split_to_ftr_test.items()
    }
    # Return the dictionaries of training and testing sets
    return n_split_to_ftr_train, n_split_to_ftr_test


def _fit_model(
    ftr_train: pd.DataFrame,
    quantile: float,
    time_col: str,
    merged_index_col: str,
    target_col: str,
    static_cols: List[str],
    freq_cols: List[str],
    freq: str,
    lags: List[int],
):
    models = [
        QuantileRegressor(solver="highs", quantile=quantile),
        LGBMRegressor(objective="quantile", alpha=quantile),
    ]

    model = MLForecast(
        models=models,
        freq=freq,
        lags=lags,
        lag_transforms={1: [expanding_mean], 2: [(rolling_mean, 4)]},
        date_features=freq_cols,
        num_threads=NUM_THREADS,
    )

    model.fit(
        data=ftr_train.set_index(merged_index_col),
        id_col="index",
        time_col=time_col,
        target_col=f"{target_col}:actual",
        static_features=static_cols,
    )

    return model


@task
def run_backtest(
    n_split_to_ftr_train: Mapping[int, pl.LazyFrame],
    n_split_to_ftr_test: Mapping[int, pl.LazyFrame],
    quantile: float,
    fit_kwargs: Mapping[str, Any],
) -> pl.LazyFrame:
    # Unpack fit_kwargs
    freq = fit_kwargs["freq"]
    time_col = fit_kwargs["time_col"]
    y_preds = []

    for n_split, ftr_train in n_split_to_ftr_train.items():
        ftr_train = ftr_train.collect().to_pandas()
        ftr_test = n_split_to_ftr_test[n_split]
        fitted_model = _fit_model(
            ftr_train=ftr_train,
            quantile=quantile,
            **fit_kwargs,
        )

        # Create "is_holiday" dynamic df from test set
        dynamic_dfs = [
            ftr_test.select(pl.col([time_col, "is_holiday"]))
            .unique()
            .collect()
            .to_pandas()
        ]

        y_pred = pl.from_pandas(
            fitted_model.predict(TEST_SIZE[freq], dynamic_dfs=dynamic_dfs).reset_index()
        ).lazy()

        y_preds.append(y_pred)

    y_preds = pl.concat(y_preds).with_column(pl.lit(quantile).alias("quantile"))
    return y_preds, fitted_model


@task
def postproc(
    y_preds: List[pl.LazyFrame],
    ftr_panel_manual: pl.LazyFrame,
    merged_index_col: str,
    time_col: str,
    target_col: str,
    allow_negatives: bool,
    use_manual_zeros: bool,
) -> pl.LazyFrame:
    y_pred = pl.concat(y_preds)

    # Average of QuantileRegressor and LGBMRegressor
    y_pred_mean = (
        y_pred.collect()
        .select(pl.all().exclude([merged_index_col, time_col, "quantile"]))
        .mean(axis=1)
        .alias(f"{target_col}:forecast")
    )

    transf_y_pred = y_pred.select(
        [pl.col([merged_index_col, time_col, "quantile"]), y_pred_mean]
    )

    if use_manual_zeros and ftr_panel_manual is not None:
        # Replace forecast to 0 according to manual forecast
        transf_y_pred = (
            transf_y_pred.join(
                ftr_panel_manual, on=[merged_index_col, time_col], how="left"
            )
            .with_column(
                pl.when(pl.col(f"{target_col}:manual") <= 0)
                .then(0)
                .otherwise(pl.col(f"{target_col}:forecast"))
                .alias(f"{target_col}:forecast")
            )
            .select(
                pl.col(
                    [
                        merged_index_col,
                        time_col,
                        "quantile",
                        f"{target_col}:forecast",
                    ]
                )
            )
        )

    if not allow_negatives:
        # Replace negative forecast to 0
        transf_y_pred = transf_y_pred.with_column(
            pl.when(pl.col(f"{target_col}:forecast") < 0)
            .then(0)
            .otherwise(pl.col(f"{target_col}:forecast"))
            .alias(f"{target_col}:forecast")
        )
    return transf_y_pred


@task
def compute_metrics(
    ftr_panel: pl.LazyFrame,
    ftr_panel_manual: pl.LazyFrame,
    backtest: pl.LazyFrame,
    quantile: float,
    time_col: str,
    merged_index_col: str,
    target_col: str,
) -> pl.LazyFrame:
    # Get backtest dates
    backtest_dates = (
        backtest.select(pl.col(time_col).unique())
        .collect()
        .get_column(time_col)
        .to_list()
    )
    # Drop additional features
    ftr_panel = ftr_panel.select([merged_index_col, time_col, f"{target_col}:actual"])
    # Drop quantile column
    backtest = backtest.select([merged_index_col, time_col, f"{target_col}:forecast"])

    forecast_mad = mad(y_true=ftr_panel, y_pred=backtest, suffix="forecast")
    forecast_smape = smape(y_true=ftr_panel, y_pred=backtest, suffix="forecast")

    if ftr_panel_manual is not None:
        # Add manual mad, smape, rank, and improvement columns
        # Filter manual forecast by backtest dates
        ftr_panel_manual = ftr_panel_manual.filter(
            pl.col(time_col).is_in(backtest_dates)
        )
        manual_mad = mad(y_true=ftr_panel, y_pred=ftr_panel_manual, suffix="manual")
        manual_smape = smape(y_true=ftr_panel, y_pred=ftr_panel_manual, suffix="manual")

        merged_mad = (
            manual_mad.join(forecast_mad, on=merged_index_col, how="outer")
            .with_column(
                # For kpi widget - total reduced over-forecast
                ((pl.col("mad:forecast") - pl.col("mad:manual")) * -1).alias(
                    "mad_improvement"
                )
            )
            .with_columns(
                [
                    (pl.col("mad_improvement") / pl.col("mad:manual") * 100).alias(
                        "mad_improvement_%"
                    ),
                    pl.col("mad:manual").rank(method="min").alias("mad_rank:manual"),
                ]
            )
        )
        merged_smape = manual_smape.join(
            forecast_smape, on=merged_index_col, how="outer"
        ).with_column(
            (
                (pl.col("smape:forecast") - pl.col("smape:manual"))
                / pl.col("smape:manual")
                * -100
            ).alias("smape_improvement_%")
        )

        metrics = merged_mad.join(merged_smape, on=merged_index_col, how="outer")
    else:
        metrics = forecast_mad.join(forecast_smape, on=merged_index_col, how="outer")

    metrics = (
        metrics
        # Reorder columns sequence - index col, quantile, others
        .select(
            [
                pl.col(merged_index_col),
                pl.lit(quantile).alias("quantile"),
                pl.col([col for col in metrics.columns if col.startswith("mad")]),
            ]
            +
            # Replace inf to 0 for smape columns
            [
                pl.when(pl.col(col).is_infinite())
                .then(0)
                .otherwise(pl.col(col))
                .keep_name()
                for col in metrics.columns
                if col.startswith("smape")
            ]
        )
    )
    return metrics


@task
def run_forecast(
    ftr_panel: pl.LazyFrame,
    quantile: float,
    fit_kwargs: Mapping[str, Any],
):
    freq = fit_kwargs["freq"]
    ftr_panel = ftr_panel.collect().to_pandas()
    fitted_model = _fit_model(ftr_train=ftr_panel, quantile=quantile, **fit_kwargs)

    # Create "is_holiday" dynamic df
    future_dates = pd.date_range(
        start=ftr_panel["time"].max(),
        freq=freq,
        periods=PRED_FH[freq] + 1,
    )[1:]
    is_holiday_df = pd.DataFrame({"time": future_dates}).assign(
        is_holiday=lambda df: df["time"].dt.month.isin([1, 2])
    )
    dynamic_dfs = [is_holiday_df]

    y_pred = (
        pl.from_pandas(
            fitted_model.predict(PRED_FH[freq], dynamic_dfs=dynamic_dfs).reset_index()
        )
        .lazy()
        .with_column(pl.lit(quantile).alias("quantile"))
    )

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


@flow
def run_forecast_flow(
    s3_data_bucket: str,
    s3_artifacts_bucket: str,
    ftr_data_paths: Mapping[str, str],
    time_col: str,
    index_cols: List[str],
    target_col: str,
    freq_cols: List[str],
    freq: str,
    lags: List[int],
    allow_negatives: bool = False,
    use_manual_zeros: bool = False,
):
    merged_index_col = ":".join(index_cols)

    # 1. Load ftr tables
    ftr_panel = load_ftr_panel(
        s3_bucket=s3_data_bucket, s3_path=ftr_data_paths["actual"]
    )
    ftr_panel_manual = None
    if "manual" in list(ftr_data_paths.keys()):
        ftr_panel_manual = load_ftr_panel(
            s3_bucket=s3_data_bucket, s3_path=ftr_data_paths["manual"]
        )

    # 2. Time series split - return mapping of n_split to LazyFrame
    static_cols = [
        col
        for col in ftr_panel.select(pl.col(pl.Boolean)).columns
        if "is_holiday" not in col
    ]

    splits_kwargs = {
        "time_col": time_col,
        "merged_index_col": merged_index_col,
        "freq": freq,
    }
    n_split_to_ftr_train, n_split_to_ftr_test = get_train_test_splits(
        ftr_panel=ftr_panel, **splits_kwargs
    )

    fit_kwargs = {
        "time_col": time_col,
        "merged_index_col": merged_index_col,
        "target_col": target_col,
        "static_cols": static_cols,
        "freq_cols": freq_cols,
        "freq": freq,
        "lags": lags,
    }
    postproc_kwargs = {
        "time_col": time_col,
        "merged_index_col": merged_index_col,
        "target_col": target_col,
        "allow_negatives": allow_negatives,
        "use_manual_zeros": use_manual_zeros,
    }

    # 3. Backtest - return backtest and fitted_model by quantile
    backtests = []
    fitted_model_by_quantile = {}
    for quantile in QUANTILES:
        backtest, fitted_model = run_backtest(
            n_split_to_ftr_train=n_split_to_ftr_train,
            n_split_to_ftr_test=n_split_to_ftr_test,
            quantile=quantile,
            fit_kwargs=fit_kwargs,
        )

        backtests.append(backtest)
        fitted_model_by_quantile[quantile] = fitted_model

    # 4. Postproc
    transf_backtests = postproc(
        y_preds=backtests, ftr_panel_manual=ftr_panel_manual, **postproc_kwargs
    )
    paths = {
        "backtests": export_panel(
            transf_backtests,
            s3_artifacts_bucket,
            ftr_data_paths["actual"],
            suffix="backtests",
        )
    }

    # 5. Compute backtest metrics by quantile
    metrics_kwargs = {
        "time_col": time_col,
        "merged_index_col": merged_index_col,
        "target_col": target_col,
    }
    metrics = []
    for quantile in QUANTILES:
        backtest_by_quantile = transf_backtests.filter(pl.col("quantile") == quantile)
        metric = compute_metrics(
            ftr_panel=ftr_panel,
            ftr_panel_manual=ftr_panel_manual,
            backtest=backtest_by_quantile,
            quantile=quantile,
            **metrics_kwargs,
        )
        metrics.append(metric)

    metrics = pl.concat(metrics)
    paths["metrics"] = export_panel(
        metrics, s3_artifacts_bucket, ftr_data_paths["actual"], suffix="metrics"
    )

    # 6. Training final model on the full dataset and predict by quantile
    y_preds = []
    for quantile in QUANTILES:
        y_pred = run_forecast(
            ftr_panel=ftr_panel,
            quantile=quantile,
            fit_kwargs=fit_kwargs,
        )
        y_preds.append(y_pred)

    transf_y_preds = postproc(
        y_preds=y_preds, ftr_panel_manual=ftr_panel_manual, **postproc_kwargs
    )
    paths["y_preds"] = export_panel(
        transf_y_preds, s3_artifacts_bucket, ftr_data_paths["actual"], suffix="y_preds"
    )

    # 7. Compute feature importance
    feature_importances = []
    for quantile in QUANTILES:
        feature_importances_by_quantile = compute_feature_importance(
            fitted_model_by_quantile, quantile
        )
        feature_importances.append(feature_importances_by_quantile)
    feature_importances = pl.concat(feature_importances)

    paths["feature_importances"] = export_panel(
        feature_importances,
        s3_artifacts_bucket,
        ftr_data_paths["actual"],
        suffix="feature_importances",
    )

    return paths
