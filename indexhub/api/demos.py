DEMO_BUCKET = "indexhub-public-trends"
DEMO_SCHEMAS = {
    "commodities": {
        "entity_col": "commodity_type",
        "vectors": "commodities/artifacts/forecasts__best_models.parquet",
        "y": "commodities/artifacts/y.parquet",
        "forecasts": "commodities/artifacts/forecasts__best_models.parquet",
        "backtests": "commodities/artifacts/backtests__best_models.parquet",
        "quantiles": "commodities/artifacts/quantiles__best_models.parquet",
    }
}
