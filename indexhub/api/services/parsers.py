import io
import json
import logging
from typing import List, Optional

import polars as pl
from fastapi import HTTPException
from polars.exceptions import ArrowError, ComputeError
from xlsx2csv import InvalidXlsxFileException


def _logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(levelname)s: %(asctime)s: %(name)s  %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # Prevent the modal client from double-logging.
    return logger


logger = _logger(name=__name__)


def parse_excel(
    obj: bytes,
    n_rows: Optional[int] = None,
    columns: Optional[List[str]] = None,
    dateformat: Optional[str] = None,
) -> pl.DataFrame:
    try:
        raw_panel = pl.read_excel(
            io.BytesIO(obj),
            # Ignore infer datatype to float as it is not supported by xlsx2csv
            xlsx2csv_options={"ignore_formats": "float", "dateformat": dateformat},
            read_csv_options={
                "infer_schema_length": None,
                "try_parse_dates": True,
                "use_pyarrow": True,
                "n_rows": n_rows,
            },
        )
    except InvalidXlsxFileException as err:
        logger.exception("❌ Error occured when parsing excel file.")
        raise HTTPException(status_code=400, detail="Invalid excel file") from err

    else:
        return raw_panel


def parse_csv(
    obj: bytes,
    n_rows: Optional[int] = None,
    columns: Optional[List[str]] = None,
    dateformat: Optional[str] = None,
) -> pl.DataFrame:
    try:
        raw_panel = pl.read_csv(io.BytesIO(obj), n_rows=n_rows)
    except ComputeError as err:
        logger.exception("❌ Error occured when parsing csv file.")
        raise HTTPException(status_code=400, detail="Invalid csv file") from err
    else:
        return raw_panel


def parse_parquet(
    obj: bytes,
    n_rows: Optional[int] = None,
    columns: Optional[List[str]] = None,
    dateformat: Optional[str] = None,
) -> pl.DataFrame:
    try:
        raw_panel = pl.read_parquet(io.BytesIO(obj), n_rows=n_rows, columns=columns)
    except ArrowError as err:
        logger.exception("❌ Error occured when parsing parquet file.")
        raise HTTPException(status_code=400, detail="Invalid parquet file") from err
    else:
        return raw_panel


def parse_json(
    obj: bytes,
    n_rows: Optional[int] = None,
    columns: Optional[List[str]] = None,
    dateformat: Optional[str] = None,
) -> dict:
    try:
        content = obj.decode("utf-8")
        data = json.loads(content)
    except json.JSONDecodeError as err:
        logger.exception("❌ Error occured when parsing json file.")
        raise HTTPException(status_code=400, detail="Invalid json file") from err
    else:
        return data
