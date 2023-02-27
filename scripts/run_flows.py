from indexhub.flows.forecasting import RunForecastFlowInput, run_forecast_flow
from indexhub.flows.preprocessing import (
    PrepareHierarchicalPanelInput,
    PreprocessPanelInput,
    prepare_hierarchical_panel,
    preprocess_panel,
)
from indexhub.flows.reporting import (
    ReportingInput,
    prepare_forecast_report,
    prepare_forecast_scenario_report,
    prepare_metrics_report,
    prepare_outliers_report,
    prepare_uplift_report,
    prepare_volatility_report,
)

S3_BUCKET = "indexhub-feature-store-934462633531"
S3_ARTIFACTS_BUCKET = "indexhub-artifact-store-934462633531"


if __name__ == "__main__":
    raw_data_path = input("Enter raw data path (default to tourism data path):")
    if not raw_data_path:
        raw_data_path = "raw/tourism_20221212.xlsx"

    manual_forecast_path = input("Enter manual forecast data path (default to None):")
    if not manual_forecast_path:
        manual_forecast_path = None

    time_col = input("Enter time column (default to 'time'):")
    if not time_col:
        time_col = "time"

    freq = input("Enter freq (default to '1mo'):")
    if not freq:
        freq = "1mo"

    target_col = input("Enter target column (default to 'trips_in_000s'):")
    if not target_col:
        target_col = "trips_in_000s"

    min_lag = input("Enter min lag (default to '1'):")
    if not min_lag:
        min_lag = 1

    max_lag = input("Enter max lag (default to '24'):")
    if not max_lag:
        max_lag = 24

    lags = list(range(min_lag, int(max_lag) + 1))

    levels = input("Enter levels (default to '['state']'):")
    if not levels:
        levels = ["state"]

    filters = input("Enter filters (default to None):")
    if not filters:
        filters = None

    agg_method = input("Enter agg method (default to 'sum'):")
    if not agg_method:
        agg_method = "sum"

    allow_negatives = input("Enter allow negatives (default to True):")
    if not allow_negatives:
        allow_negatives = True

    country_codes = input("Enter country codes (default to '['AU']'):")
    if not country_codes:
        country_codes = ["AU"]

    print("Inputs:")
    print("================================")
    print(f"raw_data_path: {raw_data_path}")
    print(f"manual_forecast_path: {manual_forecast_path}")
    print(f"time_col: {time_col}")
    print(f"freq: {freq}")
    print(f"target_col: {target_col}")
    print(f"lags: {lags}")
    print(f"levels: {levels}")
    print(f"filters: {filters}")
    print(f"country_codes: {country_codes}")
    print("================================")

    inputs = PreprocessPanelInput(
        s3_bucket=S3_BUCKET,
        time_col=time_col,
        entity_cols=levels,
        freq=freq,
        raw_data_path=raw_data_path,
        source_id=1,
        manual_forecast_path=manual_forecast_path,
        filters=filters,
    )
    paths = preprocess_panel(inputs)
    print(f"✅ Output from `preprocess_panel`: {paths}")

    fct_panel_path = paths["actual"]
    if "manual" in paths.keys():
        manual_forecasts_path = paths["manual"]
    else:
        manual_forecasts_path = None

    inputs = PrepareHierarchicalPanelInput(
        s3_bucket=S3_BUCKET,
        level_cols=levels,
        agg_method=agg_method,
        fct_panel_path=fct_panel_path,
        target_col=target_col,
        freq=freq,
        lags=lags,
        country_codes=country_codes,
        dummy_entity_cols=None,
        manual_forecasts_path=manual_forecasts_path,
        allow_negatives=allow_negatives,
    )
    ftr_data_paths = prepare_hierarchical_panel(inputs)
    print(f"✅ Output from `prepare_hierarchical_panel`: {ftr_data_paths}")

    inputs = RunForecastFlowInput(
        s3_data_bucket=S3_BUCKET,
        s3_artifacts_bucket=S3_ARTIFACTS_BUCKET,
        ftr_data_paths=ftr_data_paths,
        s3_tscatalog_bucket=None,
        external_data_paths=None,
        freq=freq,
        lags=lags,
        dummy_entity_cols=None,
        allow_negatives=allow_negatives,
        use_manual_zeros=False,
    )
    forecast_data_paths = run_forecast_flow(inputs)
    print(f"✅ Output from `run_forecast_flow`: {forecast_data_paths}")

    inputs = ReportingInput(
        s3_data_bucket=S3_BUCKET,
        s3_artifacts_bucket=S3_ARTIFACTS_BUCKET,
        ftr_data_paths=ftr_data_paths,
        forecast_data_paths=forecast_data_paths,
        level_cols=levels,
    )

    rpt_metrics_paths = prepare_metrics_report(inputs)
    rpt_forecast_paths = prepare_forecast_report(inputs)
    rpt_forecast_scenario_paths = prepare_forecast_scenario_report(inputs)
    rpt_volatility_paths = prepare_volatility_report(inputs)
    rpt_outliers_paths = prepare_outliers_report(inputs)
    rpt_uplift_paths = prepare_uplift_report(inputs)

    print(f"✅ Output from `prepare_metrics_report`: {rpt_metrics_paths}")
    print(f"✅ Output from `prepare_forecast_report`: {rpt_forecast_paths}")
    print(
        f"✅ Output from `prepare_forecast_scenario_report`: {rpt_forecast_scenario_paths}"
    )
    print(f"✅ Output from `prepare_volatility_report`: {rpt_volatility_paths}")
    print(f"✅ Output from `prepare_outliers_report`: {rpt_outliers_paths}")
    print(f"✅ Output from `prepare_uplift_report`: {rpt_uplift_paths}")
