import json
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


def SOURCE_SCHEMAS(user: User):
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
            "freq": "",
            "datetime_fmt": "%Y-%m-%d",
            "columns": {
                "entity_cols": [],
                "time_col": "",
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
            "freq": "",
            "datetime_fmt": "%Y-%m-%d",
            "columns": {
                "entity_cols": [],
                "time_col": "",
            },
        },
    }


def TARGET_COL_SCHEMA(sources: List[Source], depends_on: str = "source_id"):
    schema = {
        "title": "Target column",
        "subtitle": "Target column to forecast such as quantity, sales amount, etc.",
        # Probably won't scale but good enough for now
        "values": {src.id: json.loads(src.columns)["feature_cols"] for src in sources},
        "depends_on": depends_on,
    }
    return schema


def LEVEL_COLS_SCHEMA(sources: List[Source], depends_on: str = "source_id"):
    schema = {
        "title": "Level column(s)",
        "subtitle": "Run forecast by levels such as region, customer, product category, etc.",
        # Probably won't scale but good enough for now
        "values": {src.id: json.loads(src.columns)["entity_cols"] for src in sources},
        "depends_on": depends_on,
        "multiple_choice": True,
    }
    return schema


def INVOICE_COL_SCHEMA(sources: List[Source], depends_on: str = "source_id"):
    schema = {
        "title": "Invoice ID column",
        "subtitle": "Represents the ID for a basket of orders or a single trip",
        "values": {src.id: json.loads(src.columns)["feature_cols"] for src in sources},
        "depends_on": depends_on,
    }
    return schema


def PRODUCT_COL_SCHEMA(sources: List[Source], depends_on: str = "source_id"):
    schema = {
        "title": "Product ID column",
        "subtitle": "Represents the column of products / services (e.g. SKU)",
        "values": {src.id: json.loads(src.columns)["feature_cols"] for src in sources},
        "depends_on": depends_on,
    }
    return schema


def SOURCES_SCHEMA(sources: List[Source]):
    return {
        "panel": {
            "title": "Dataset",
            "subtitle": "Select one panel dataset of observed values to forecast.",
            "values": {src.name: src.id for src in sources},
        },
        "baseline": {
            "title": "Baseline Forecasts",
            "subtitle": (
                "Select one panel dataset of forecasted values to benchmark the AI prediction model against."
                " Must have the same schema as `panel`."
                " Note: If this is not specified, a seasonal naive/naive forecast will be automatically generated and used as a baseline."
            ),
            "values": {src.name: src.id for src in sources},
            "is_required": False,
        },
        "inventory": {
            "title": "Inventory",
            "subtitle": (
                "Select one inventory dataset." " Must have the same schema as `panel`."
            ),
            "values": {src.name: src.id for src in sources},
            "is_required": False,
        },
    }


def FIELDS_SCHEMA(sources: List[Source]):
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
        "target_col": TARGET_COL_SCHEMA(sources=sources, depends_on="panel"),
        "level_cols": LEVEL_COLS_SCHEMA(sources=sources, depends_on="panel"),
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
        "freq": {
            "title": "Frequency",
            "subtitle": "How often do you want to generate new predictions?",
            "values": list(SUPPORTED_FREQ.keys()),
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
        "agg_method": {
            "title": "Aggregation Method",
            "subtitle": "How do you want to aggregate the target after group by levels?",
            "values": ["sum", "mean", "median"],
        },
        "impute_method": {
            "title": "Imputation Method",
            "subtitle": "How do you want to impute the target if there is missing data?",
            "values": [0, "mean", "median", "fill", "ffill", "bfill", "interpolate"],
        },
    }


def POLICY_SCHEMAS(sources: List[Source]):
    schemas = {
        "forecast_panel": {
            "objective": "{direction} {target_col} {error_type} for {level_cols}.",
            "description": "Choose this policy if you have panel data (i.e. time-series data across multiple entities).",
            "sources": SOURCES_SCHEMA(sources),
            "fields": {
                **FIELDS_SCHEMA(sources),
                "goal": {
                    "title": "Goal",
                    "subtitle": "What percentage (%) reduction of forecast error do you plan to achieve?",
                    "values": list(range(1, 99)),
                    "default": 15,
                },
            },
        },
        "forecast_transaction": {
            "objective": "{direction} {target_col} {error_type} for {level_cols}.",
            "description": "Choose this policy if you have transactions data (e.g. point-of-sales).",
            "sources": {
                **SOURCES_SCHEMA(sources),
                "transaction": {
                    "title": "Transaction Dataset",
                    "subtitle": (
                        "Select one dataset of transactions (e.g. point-of-sales data) to forecast."
                        " Must include columns specifying the invoice ID and the product ID."
                    ),
                    "values": {src.name: src.id for src in sources},
                },
            },
            "fields": {
                **FIELDS_SCHEMA(sources),
                "invoice_col": INVOICE_COL_SCHEMA(
                    sources=sources, depends_on="transaction"
                ),
                "product_col": PRODUCT_COL_SCHEMA(
                    sources=sources, depends_on="transaction"
                ),
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
