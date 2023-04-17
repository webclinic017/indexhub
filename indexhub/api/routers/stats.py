import json
from functools import partial
from typing import List, Mapping

import polars as pl
from fastapi import APIRouter
from sqlmodel import Session

from indexhub.api.db import engine
from indexhub.api.models.user import User
from indexhub.api.routers.policies import get_policy
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret

router = APIRouter()

FREQ_NAME_TO_LABEL = {
    "Hourly": "hours",
    "Daily": "days",
    "Weekly": "weeks",
    "Monthly": "months",
}

ERROR_TYPE_TO_METRIC = {
    "over-forecast": "overforecast",
    "under-forecast": "underforecast",
    "both over-forecast and under-forecast": "mae",
}


# STATS RESULT TABLES
def _get_forecast_results(
    outputs: Mapping[str, str], fields: Mapping[str, str], user: User, policy_id: str
) -> pl.DataFrame:
    # Get credentials
    storage_creds = get_aws_secret(
        tag=user.storage_tag, secret_type="storage", user_id=user.id
    )
    read = partial(
        SOURCE_TAG_TO_READER[user.storage_tag],
        bucket_name=user.storage_bucket_name,
        file_ext="parquet",
        **storage_creds,
    )

    # Read artifacts
    y = read(object_path=outputs["y"]).lazy()
    best_model = outputs["best_model"]
    forecasts = read(object_path=outputs["forecasts"][best_model])
    backtests = read(object_path=outputs["backtests"][best_model])
    statistics = read(object_path=outputs["statistics"]["last_window__sum"])
    uplift = read(object_path=outputs["uplift"])
    rolling_uplift = read(object_path=f"artifacts/{policy_id}/rolling_uplift.parquet")

    entity_col, time_col, target_col = y.columns

    results = []
    fh = forecasts.get_column(time_col).n_unique()
    freq = FREQ_NAME_TO_LABEL[fields["freq"]]
    backtest_period = backtests.get_column(time_col).n_unique()

    # Target to date for last fh
    target_to_date = statistics.get_column(target_col).sum()
    stats_target_to_date = {
        "title": f"{target_col} to date",
        "subtitle": f"Last {fh} {freq}",
        "values": {"sum": round(target_to_date, 2)},
    }
    results.append(stats_target_to_date)

    # AI predicted for next fh
    forecast_value = forecasts.get_column(target_col).sum()
    forecast_change = forecast_value - target_to_date
    forecast_pct_change = (forecast_change / target_to_date) * 100

    stats_forecast = {
        "title": "AI Predicted (Forecast)",
        "subtitle": f"Next {fh} {freq}",
        "values": {
            "sum": round(forecast_value, 2),
            "diff": round(forecast_change, 2),
            "pct_change": round(forecast_pct_change, 2),
        },
    }
    results.append(stats_forecast)

    # AI predicted uplift for next fh
    metric = ERROR_TYPE_TO_METRIC[fields["error_type"]]
    uplift_value = uplift.get_column(f"{metric}__uplift").sum()
    uplift_pct = (
        uplift.with_columns(
            # Replace inf with null
            pl.when(pl.col(f"{metric}__uplift_pct").is_infinite())
            .then(None)
            .otherwise(pl.col(f"{metric}__uplift_pct"))
            .keep_name()
        )
        .get_column(f"{metric}__uplift_pct")
        .mean()
        * 100
    )

    stats_uplift = {
        "title": "AI Uplift",
        "subtitle": f"Backtest results over the last {backtest_period} {freq}",
        "values": {"sum": round(uplift_value, 2), "mean_pct": round(uplift_pct, 2)},
    }
    results.append(stats_uplift)

    # AI predicted rolling_uplift for next fh
    rolling_mean_uplift_pct = (
        rolling_uplift.sort([entity_col, "updated_at"])
        .groupby([entity_col])
        .tail(1)
        .get_column(f"{metric}__uplift_pct__rolling_mean")
        .mean()
        * 100
    )

    stats_uplift = {
        "title": "AI Uplift (Cumulative)",
        "subtitle": f"Average uplift percentage over the last {backtest_period} {freq}",
        "values": {
            "rolling_mean_pct": round(rolling_mean_uplift_pct, 2),
        },
    }
    results.append(stats_uplift)

    return results


POLICY_TAG_TO_GETTER = {"forecast": _get_forecast_results}


@router.get("/tables/{policy_id}")
def get_stats(
    policy_id: str,
) -> List[Mapping[str, str]]:
    with Session(engine) as session:
        policy = get_policy(policy_id)["policy"]
        getter = POLICY_TAG_TO_GETTER[policy.tag]
        user = session.get(User, policy.user_id)
        stats = getter(
            json.loads(policy.outputs), json.loads(policy.fields), user, policy_id
        )  # TODO: Cache using an in memory key-value store
    return stats
