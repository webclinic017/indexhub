DEMO_BUCKET = "indexhub-public-trends"
DEMO_SCHEMAS = {
    "commodities": {
        "entity_col": "commodity_type",
        "vectors": "vectors/commodities.lance",
        "y": "commodities/artifacts/y.parquet",
        "forecasts": "commodities/artifacts/forecasts__best_models.parquet",
        "backtests": "commodities/artifacts/backtests__best_models.parquet",
        "quantiles": "commodities/artifacts/quantiles__best_models.parquet",
        "metadata": "commodities/metadata.json",
    },
    "commercial_real_estate": {
        "entity_col": "district__grade",
        "vectors": "vectors/commercial_real_estate.lance",
        "y": "commercial_real_estate/artifacts/y.parquet",
        "forecasts": "commercial_real_estate/artifacts/forecasts__best_models.parquet",
        "backtests": "commercial_real_estate/artifacts/backtests__best_models.parquet",
        "quantiles": "commercial_real_estate/artifacts/quantiles__best_models.parquet",
        "metadata": "commercial_real_estate/metadata.json",
    },
    "econdb_cpi": {
        "entity_col": "iso_country_code",
        "vectors": "vectors/econdb_cpi.lance",
        "y": "econdb_cpi/artifacts/y.parquet",
        "forecasts": "econdb_cpi/artifacts/forecasts__best_models.parquet",
        "backtests": "econdb_cpi/artifacts/backtests__best_models.parquet",
        "quantiles": "econdb_cpi/artifacts/quantiles__best_models.parquet",
        "metadata": "econdb_cpi/metadata.json",
    },
}
