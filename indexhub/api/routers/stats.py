import json
from functools import partial
from typing import Any, List, Mapping

import polars as pl
from sqlmodel import Session

from indexhub.api.db import create_sql_engine
from indexhub.api.models.user import User
from indexhub.api.routers import router
from indexhub.api.routers.objectives import FREQ_TO_SP, get_objective
from indexhub.api.routers.sources import get_source
from indexhub.api.schemas import SUPPORTED_ERROR_TYPE
from indexhub.api.services.io import SOURCE_TAG_TO_READER
from indexhub.api.services.secrets_manager import get_aws_secret


FREQ_NAME_TO_LABEL = {
    "Hourly": "hours",
    "Daily": "days",
    "Weekly": "weeks",
    "Monthly": "months",
}


AGG_METHODS = {"sum": pl.sum, "mean": pl.mean, "median": pl.median}


# STATS RESULT TABLES
def _get_forecast_results(
    outputs: Mapping[str, str],
    fields: Mapping[str, str],
    source_fields: Mapping[str, str],
    user: User,
    objective_id: str,
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
    forecasts = read(object_path=outputs["forecasts"]["best_models"])
    backtests = read(object_path=outputs["backtests"]["best_models"])
    fields_agg_method = source_fields.get("agg_method", "sum")
    agg_method = AGG_METHODS[fields_agg_method]
    statistics = read(
        object_path=outputs["statistics"][f"last_window__{fields_agg_method}"]
    )
    uplift = read(object_path=outputs["uplift"])
    rolling_uplift = read(
        object_path=f"artifacts/{objective_id}/rolling_uplift.parquet"
    )

    entity_col, time_col, target_col = y.columns
    target_col_label = target_col.replace("_", " ").capitalize()

    results = []
    fh = forecasts.get_column(time_col).n_unique()
    freq = FREQ_NAME_TO_LABEL[source_fields["freq"]]
    sp = FREQ_TO_SP[source_fields["freq"]]
    backtest_period = backtests.get_column(time_col).n_unique()

    # Target to date for last fh
    target_to_date = statistics.select(agg_method(target_col)).get_column(target_col)[0]
    stats_target_to_date = {
        "title": f"{target_col_label} to date",
        "subtitle": f"Over the last {fh} {freq}",
        "values": {"sum": round(target_to_date, 2)},
    }
    results.append(stats_target_to_date)

    # AI predicted for next fh
    forecast_value = forecasts.select(agg_method(target_col)).get_column(target_col)[0]
    forecast_change = forecast_value - target_to_date
    forecast_pct_change = (forecast_change / target_to_date) * 100

    stats_forecast = {
        "title": f"AI Forecast of {target_col_label}",
        "subtitle": f"Over next {fh} {freq}",
        "values": {
            "sum": round(forecast_value, 2),
            "diff": round(forecast_change, 2),
            "pct_change": round(forecast_pct_change, 2),
        },
    }
    results.append(stats_forecast)

    # AI predicted uplift for next fh
    metric = SUPPORTED_ERROR_TYPE[fields["error_type"]]
    # Select uplift where AI is better than baseline
    uplift_filtered = uplift.filter(pl.col(f"{metric}__uplift") >= 0)
    uplift_value = uplift_filtered.select(agg_method(f"{metric}__uplift")).get_column(
        f"{metric}__uplift"
    )[0]
    uplift_pct = (
        uplift_filtered.with_columns(
            # Replace inf with null
            pl.when(pl.col(f"{metric}__uplift_pct").is_infinite())
            .then(None)
            .otherwise(
                pl.when(pl.col(f"{metric}__uplift_pct") < 0)
                .then(0)
                .otherwise(pl.col(f"{metric}__uplift_pct"))
            )
            .keep_name()
        )
        .get_column(f"{metric}__uplift_pct")
        .fill_nan(None)
        .mean()
        * 100
    )

    stats_uplift = {
        "title": "AI Uplift",
        "subtitle": f"Backtest results over past {backtest_period} {freq}",
        "values": {"sum": round(uplift_value, 2), "mean_pct": round(uplift_pct, 2)},
    }
    results.append(stats_uplift)

    # AI predicted rolling_uplift for next fh
    rolling_uplift_grouped = (
        rolling_uplift.sort([entity_col, "updated_at"])
        .groupby([entity_col])
        .tail(1)
        .with_columns(pl.col(f"{metric}__uplift_pct__rolling_mean") * 100)
    )
    rolling_agg_uplift = rolling_uplift_grouped.select(
        agg_method(f"{metric}__uplift__rolling_{fields_agg_method}")
    ).get_column(f"{metric}__uplift__rolling_{fields_agg_method}")[0]
    rolling_mean_uplift_pct = (
        rolling_uplift_grouped.with_columns(
            pl.when(pl.col(f"{metric}__uplift_pct__rolling_mean") < 0)
            .then(0)
            .otherwise(pl.col(f"{metric}__uplift_pct__rolling_mean"))
            .keep_name()
        )
        .get_column(f"{metric}__uplift_pct__rolling_mean")
        .fill_nan(None)
        .mean()
    )

    stats_rolling_uplift = {
        "title": "AI Uplift (Cumulative)",
        "subtitle": f"Cumulative uplift (last {sp} {freq})",
        "values": {
            "rolling_sum": round(rolling_agg_uplift, 2),
            "rolling_mean_pct": round(rolling_mean_uplift_pct, 2),
        },
    }
    results.append(stats_rolling_uplift)

    # Count of AI improvements
    n_improvement = (
        rolling_uplift_grouped.filter(
            pl.col(f"{metric}__uplift_pct__rolling_mean") >= 0
        )
        .get_column(entity_col)
        .n_unique()
    )
    n_entities = rolling_uplift_grouped.get_column(entity_col).n_unique()
    stats_improvement_count = {
        "title": "AI Improvements",
        "subtitle": "Number of entities with improvements using AI",
        "values": {"n_improvement": n_improvement, "n_entities": n_entities},
    }
    results.append(stats_improvement_count)

    # Goal
    goal = fields["goal"]
    stats_goal = {
        "title": "Goal",
        "subtitle": f"Goal for average uplift % (last {sp} {freq})",
        "values": {"goal": goal},
    }
    results.append(stats_goal)

    # Progress
    progress = round(rolling_mean_uplift_pct / goal * 100, 2)
    if progress > 100:
        progress = 100
    stats_progress = {
        "title": "Progress",
        "subtitle": "Average uplift % towards goal",
        "values": {"progress": progress},
    }
    results.append(stats_progress)

    # Count of entities achieved goal
    n_achievement = (
        rolling_uplift_grouped.filter(
            pl.col(f"{metric}__uplift_pct__rolling_mean") >= goal
        )
        .get_column(entity_col)
        .n_unique()
    )
    stats_achievement = {
        "title": "Achievement",
        "subtitle": "Number of entities achieved goal",
        "values": {"n_achievement": n_achievement, "n_entities": n_entities},
    }
    results.append(stats_achievement)

    return results


OBJECTIVE_TAG_TO_GETTER = {"reduce_errors": _get_forecast_results}


@router.get("/stats/{objective_id}")
def get_stats(
    objective_id: str,
) -> List[Mapping[str, Any]]:
    engine = create_sql_engine()
    with Session(engine) as session:
        objective = get_objective(objective_id)["objective"]
        getter = OBJECTIVE_TAG_TO_GETTER[objective.tag]
        user = session.get(User, objective.user_id)
        source = get_source(json.loads(objective.sources)["panel"])["source"]
        stats = getter(
            json.loads(objective.outputs),
            json.loads(objective.fields),
            json.loads(source.data_fields),
            user,
            objective_id,
        )  # TODO: Cache using an in memory key-value store
    return stats
