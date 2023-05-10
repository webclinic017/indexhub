from typing import List

from indexhub.api.models.source import Source
from indexhub.api.models.user import User


SUPPORTED_COUNTRIES = {
    "Andorra": "AD",
    "United Arab Emirates": "AE",
    "Albania": "AL",
    "Armenia": "AM",
    "Angola": "AO",
    "Argentina": "AR",
    "American Samoa": "AS",
    "Austria": "AT",
    "Australia": "AU",
    "Aruba": "AW",
    "Azerbaijan": "AZ",
    "Bosnia and Herzegovina": "BA",
    "Bangladesh": "BD",
    "Belgium": "BE",
    "Bulgaria": "BG",
    "Bahrain": "BH",
    "Burundi": "BI",
    "Bolivia, Plurinational State of": "BO",
    "Brazil": "BR",
    "Botswana": "BW",
    "Belarus": "BY",
    "Canada": "CA",
    "Switzerland": "CH",
    "Chile": "CL",
    "China": "CN",
    "Colombia": "CO",
    "Costa Rica": "CR",
    "Cuba": "CU",
    "Curaçao": "CW",
    "Cyprus": "CY",
    "Czechia": "CZ",
    "Germany": "DE",
    "Djibouti": "DJ",
    "Denmark": "DK",
    "Dominican Republic": "DO",
    "Estonia": "EE",
    "Egypt": "EG",
    "Spain": "ES",
    "Ethiopia": "ET",
    "Finland": "FI",
    "France": "FR",
    "United Kingdom": "GB",
    "Georgia": "GE",
    "Greece": "GR",
    "Guam": "GU",
    "Hong Kong": "HK",
    "Honduras": "HN",
    "Croatia": "HR",
    "Hungary": "HU",
    "Indonesia": "ID",
    "Ireland": "IE",
    "Israel": "IL",
    "Isle of Man": "IM",
    "India": "IN",
    "Iceland": "IS",
    "Italy": "IT",
    "Jamaica": "JM",
    "Japan": "JP",
    "Kenya": "KE",
    "Kyrgyzstan": "KG",
    "Korea, Republic of": "KR",
    "Kazakhstan": "KZ",
    "Liechtenstein": "LI",
    "Lesotho": "LS",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Latvia": "LV",
    "Morocco": "MA",
    "Monaco": "MC",
    "Moldova, Republic of": "MD",
    "Montenegro": "ME",
    "Madagascar": "MG",
    "Marshall Islands": "MH",
    "North Macedonia": "MK",
    "Northern Mariana Islands": "MP",
    "Malta": "MT",
    "Malawi": "MW",
    "Mexico": "MX",
    "Malaysia": "MY",
    "Mozambique": "MZ",
    "Namibia": "NA",
    "Nigeria": "NG",
    "Nicaragua": "NI",
    "Netherlands": "NL",
    "Norway": "NO",
    "New Zealand": "NZ",
    "Panama": "PA",
    "Peru": "PE",
    "Philippines": "PH",
    "Pakistan": "PK",
    "Poland": "PL",
    "Puerto Rico": "PR",
    "Portugal": "PT",
    "Paraguay": "PY",
    "Romania": "RO",
    "Serbia": "RS",
    "Russian Federation": "RU",
    "Saudi Arabia": "SA",
    "Sweden": "SE",
    "Singapore": "SG",
    "Slovenia": "SI",
    "Slovakia": "SK",
    "San Marino": "SM",
    "Eswatini": "SZ",
    "Thailand": "TH",
    "Tunisia": "TN",
    "Turkey": "TR",
    "Taiwan, Province of China": "TW",
    "Ukraine": "UA",
    "United States Minor Outlying Islands": "UM",
    "United States": "US",
    "Uruguay": "UY",
    "Uzbekistan": "UZ",
    "Holy See (Vatican City State)": "VA",
    "Venezuela, Bolivarian Republic of": "VE",
    "Virgin Islands, U.S.": "VI",
    "Viet Nam": "VN",
    "South Africa": "ZA",
    "Zambia": "ZM",
    "Zimbabwe": "ZW",
}

SUPPORTED_ERROR_TYPE = {
    "over-forecast": "overforecast",
    "under-forecast": "underforecast",
    "mean absolute error (MAE)": "mae",
    "over and under forecast (mean forecast error)": "mfe",
    "symmetric mean absolute percentage error (SMAPE)": "smape",
    "mean absolute scaled error (MASE)": "mase",
    "root mean scaled squared error (RMSSE)": "rmsse",
}

SUPPORTED_FREQ = {
    "Hourly": "1h",
    "Daily": "1d",
    "Weekly": "1w",
    "Monthly": "1mo",
}

SUPPORTED_DIRECTION = {
    "Maximize": "max",
    "Minimize": "min",
}

STORAGE_SCHEMAS = {
    "s3": {
        "AWS_ACCESS_KEY_ID": {
            "title": "AWS Access Key ID",
            "subtitle": "Equivalent to the AWS_ACCESS_KEY_ID environment variable.",
        },
        "AWS_SECRET_KEY_ID": {
            "title": "AWS Secret Key ID",
            "subtitle": "Equivalent to the AWS_SECRET_ACCESS_KEY environment variable.",
        },
    },
    # Schema for Azure Blob Storage taken from:
    # https://docs.prefect.io/api-ref/prefect/filesystems/#prefect.filesystems.Azure
    "azure": {
        "AZURE_STORAGE_CONNECTION_STRING": {
            "title": "Azure storage connection string",
            "subtitle": "Equivalent to the AZURE_STORAGE_CONNECTION_STRING environment variable.",
        },
        "AZURE_STORAGE_ACCOUNT_KEY": {
            "title": "Azure storage account key",
            "subtitle": "Equivalent to the AZURE_STORAGE_ACCOUNT_KEY environment variable.",
        },
        "AZURE_TENANT_ID": {
            "title": "Azure storage tenant ID",
            "subtitle": "Equivalent to the AZURE_TENANT_ID environment variable.",
        },
    },
}

SUPPORTED_FILE_EXT = {
    "title": "File extension",
    "subtitle": "",
    "values": ["csv", "xlsx", "parquet"],
}


SUPPORTED_BASELINE_MODELS = {
    "Seasonal Naive": "snaive",
    "Naive": "naive",
}


TIME_COL_SCHEMA = {
    "title": "Product ID column",
    "subtitle": "Represents the column of products / services (e.g. SKU)",
    "values": "",
}


TARGET_COL_SCHEMA = {
    "title": "Target column",
    "subtitle": "Target column to forecast such as quantity, sales amount, etc.",
    "values": "",
}


ENTITY_COLS_SCHEMA = {
    "title": "Entity column(s)",
    "subtitle": "Run forecast by entity columns such as region, customer, product category, etc.",
    "values": [],
}

INVOICE_COL_SCHEMA = {
    "title": "Invoice ID column",
    "subtitle": "Represents the ID for a basket of orders or a single trip",
    "values": "",
}


PRODUCT_COL_SCHEMA = {
    "title": "Product ID column",
    "subtitle": "Represents the column of products / services (e.g. SKU)",
    "values": "",
}


PRICE_COL_SCHEMA = {
    "title": "Price column",
    "subtitle": "Represents the column for prices of items at the time of purchase",
    "values": "",
}


QUANTITY_COL_SCHEMA = {
    "title": "Quantity column",
    "subtitle": "Represents the column for quantities sold at the time of purchase",
    "values": "",
}


FEATURE_COLS_SCHEMA = {
    "title": "Features column",
    "subtitle": "Represents the additional columns/features that are optional and might be useful in improving forecast results",
    "values": [],
}


AGG_METHOD_SCHEMA = {
    "title": "Aggregation Method",
    "subtitle": "How do you want to aggregate the target after group by entity columns?",
    "values": ["sum", "mean", "median"],
    "is_required": False,
}


IMPUTE_METHOD_SCHEMA = {
    "title": "Imputation Method",
    "subtitle": "How do you want to impute the target if there is missing data?",
    "values": [
        0,
        "mean",
        "median",
        "fill",
        "ffill",
        "bfill",
        "interpolate",
    ],
    "is_required": False,
}


def SOURCES_SCHEMA(sources: List[Source], type: str):
    return {
        "panel": {
            "title": "Dataset",
            "subtitle": "Select one panel dataset of observed values to forecast.",
            "values": {src.name: src.id for src in sources if src.type == type},
        },
        "baseline": {
            "title": "Baseline Forecasts",
            "subtitle": (
                "Select one panel dataset of forecasted values to benchmark the AI prediction model against."
                " Must have the same schema as `panel`."
                " Note: If this is not specified, a seasonal naive/naive forecast will be automatically generated and used as a baseline."
            ),
            "values": {src.name: src.id for src in sources if src.type == type},
            "is_required": False,
        },
        "inventory": {
            "title": "Inventory",
            "subtitle": (
                "Select one inventory dataset." " Must have the same schema as `panel`."
            ),
            "values": {src.name: src.id for src in sources if src.type == type},
            "is_required": False,
        },
    }


def OBJECTIVE_FIELDS_SCHEMA():
    return {
        "direction": {
            "title": "Forecast Direction",
            "subtitle": "What should the forecasting model focus on?",
            "values": list(SUPPORTED_DIRECTION.keys()),
        },
        "error_type": {
            "title": "Forecast Error Type",
            "subtitle": "Which type of forecast error do you want to reduce?",
            "values": list(SUPPORTED_ERROR_TYPE.keys()),
        },
        "min_lags": {
            "title": "What is the minimum number lagged variables?",
            "subtitle": "`min_lags` must be less than `max_lags`.",
            "values": list(range(12, 25)),
            "default": 12,
        },
        "max_lags": {
            "title": "What is the maximum number of lagged variables?",
            "subtitle": "`max_lags` must be greater than `min_lags`.",
            "values": list(range(24, 49)),
            "default": 24,
        },
        "fh": {
            "title": "Forecast Horizon",
            "subtitle": "How many periods into the future do you want to predict?",
            "values": list(range(1, 30)),
        },
        "holiday_regions": {
            "title": "Holiday Regions",
            "subtitle": "Include holiday effects from a list of supported countries into the AI prediction model",
            "values": list(SUPPORTED_COUNTRIES.keys()),
        },
        "baseline_model": {
            "title": "Baseline Model",
            "subtitle": "Which model do you want to use to train the baseline forecasts?",
            "values": list(SUPPORTED_BASELINE_MODELS.keys()),
        },
    }


SOURCE_FIELDS_SCHEMA = {
    "panel": {
        "description": "Choose this source if you have panel data (i.e. time-series data across multiple entities).",
        "fields": {
            "entity_cols": ENTITY_COLS_SCHEMA,
            "time_col": TIME_COL_SCHEMA,
            "target_col": TARGET_COL_SCHEMA,
            "feature_cols": FEATURE_COLS_SCHEMA,
            "agg_method": AGG_METHOD_SCHEMA,
            "impute_method": IMPUTE_METHOD_SCHEMA,
            "freq": SUPPORTED_FREQ,
            "datetime_fmt": "%Y-%m-%d",
        },
    },
    "transaction": {
        "description": "Choose this source if you have transactions data (e.g. point-of-sales).",
        "fields": {
            "entity_cols": ENTITY_COLS_SCHEMA,
            "time_col": TIME_COL_SCHEMA,
            "target_col": TARGET_COL_SCHEMA,
            "quantity_col": QUANTITY_COL_SCHEMA,
            "price_col": PRICE_COL_SCHEMA,
            "invoice_col": INVOICE_COL_SCHEMA,
            "product_col": PRODUCT_COL_SCHEMA,
            "feature_cols": FEATURE_COLS_SCHEMA,
            "agg_method": AGG_METHOD_SCHEMA,
            "impute_method": IMPUTE_METHOD_SCHEMA,
            "freq": SUPPORTED_FREQ,
            "datetime_fmt": "%Y-%m-%d",
        },
    },
}


def CONNECTION_SCHEMA(user: User):
    return {
        "s3": {
            "available": True,
            "is_authenticated": user.has_s3_creds,
            "credentials": STORAGE_SCHEMAS["s3"],
            "description": "",
            "variables": {
                "bucket_name": {
                    "title": "Bucket name",
                    "subtitle": "",
                },
                "object_path": {
                    "title": "Object path",
                    "subtitle": "",
                },
                "file_ext": SUPPORTED_FILE_EXT,
            },
        },
        "azure": {
            "available": False,
            "is_authenticated": user.has_azure_creds,
            "credentials": STORAGE_SCHEMAS["azure"],
            "description": "",
            "variables": {
                "bucket_name": {
                    "title": "Bucket name",
                    "subtitle": "",
                },
                "object_path": {
                    "title": "Object path",
                    "subtitle": "",
                },
                "file_ext": SUPPORTED_FILE_EXT,
            },
        },
    }


def SOURCE_SCHEMAS(user: User):
    """User input schemas for source selection."""
    return {
        "s3": {
            "panel": {
                **CONNECTION_SCHEMA(user)["s3"],
                "fields": SOURCE_FIELDS_SCHEMA["panel"],
                "type": ["panel", "baseline", "inventory"],
            },
            "transaction": {
                **CONNECTION_SCHEMA(user)["s3"],
                "fields": SOURCE_FIELDS_SCHEMA["transaction"],
                "type": ["panel", "baseline", "inventory", "transaction"],
            },
        },
        "azure": {
            "panel": {
                **CONNECTION_SCHEMA(user)["azure"],
                "fields": SOURCE_FIELDS_SCHEMA["panel"],
                "type": ["panel", "baseline", "inventory"],
            },
            "transaction": {
                **CONNECTION_SCHEMA(user)["azure"],
                "fields": SOURCE_FIELDS_SCHEMA["transaction"],
                "type": ["panel", "baseline", "inventory", "transaction"],
            },
        },
    }


def OBJECTIVE_SCHEMAS(sources: List[Source]):
    """User input schemas for objective selection."""
    schemas = {
        "reduce_errors": {
            "objective": "{direction} {target_col} {error_type} for {entity_cols}.",
            "description": "This objective is suitable for forecasting sales, demands on items, inventory, prices, etc.",
            "sources": SOURCES_SCHEMA(sources, type="panel"),
            "fields": {
                **OBJECTIVE_FIELDS_SCHEMA(),
                "goal": {
                    "title": "Goal",
                    "subtitle": "What percentage (%) reduction of forecast error do you plan to achieve?",
                    "values": list(range(1, 99)),
                    "default": 15,
                },
            },
        },
    }
    return schemas
