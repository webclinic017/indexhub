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
        "subtitle": "Run forecast by levels such as region, customer, product, etc.",
        # Probably won't scale but good enough for now
        "values": {src.id: json.loads(src.columns)["entity_cols"] for src in sources},
        "depends_on": depends_on,
        "multiple_choice": True,
    }
    return schema


def POLICY_SCHEMAS(sources: List[Source]):
    schemas = {
        "forecast": {
            "objective": "Reduce {target_col} {error_type} for {level_cols} segmented by {segmentation_factor}.",
            "description": "Choose this policy to reduce .",
            "sources": {
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
                    ),
                    "values": {src.name: src.id for src in sources},
                    "is_required": False,
                },
            },
            "fields": {
                "error_type": {
                    "title": "Forecast Error Type",
                    "subtitle": "Which type of forecast error do you want to reduce?",
                    "values": [
                        "over-forecast",
                        "under-forecast",
                        "both over-forecast and under-forecast",
                    ],
                },
                "segmentation_factor": {
                    "title": "Segmentation Factor",
                    "subtitle": "How do you want to segment the AI predictions?",
                    "values": [
                        "volatlity",
                        "total value",
                        "historical growth rate",
                        "predicted growth rate",
                    ],
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
                    "values": ["Hourly", "Daily", "Weekly", "Monthly"],
                },
                "holiday_regions": {
                    "title": "Holiday Regions",
                    "subtitle": "Include holiday effects from a list of supported countries into the AI prediction model",
                    "values": list(SUPPORTED_COUNTRIES.keys()),
                },
            },
        }
    }
    return schemas
