import io
from typing import Optional

import polars as pl
from fastapi import HTTPException
from polars.exceptions import ArrowError, ComputeError
from xlsx2csv import InvalidXlsxFileException


def parse_excel(obj: str, n_rows: Optional[int] = None) -> pl.DataFrame:
    try:
        raw_panel = pl.read_excel(
            io.BytesIO(obj),
            # Ignore infer datatype to float as it is not supported by xlsx2csv
            xlsx2csv_options={"ignore_formats": "float"},
            read_csv_options={
                "infer_schema_length": None,
                "parse_dates": True,
                "use_pyarrow": True,
                "n_rows": n_rows,
            },
        )
    except InvalidXlsxFileException as err:
        raise HTTPException(status_code=400, detail="Invalid excel file") from err

    else:
        return raw_panel


def parse_csv(obj: str, n_rows: Optional[int] = None):
    try:
        raw_panel = pl.read_csv(io.BytesIO(obj), n_rows=n_rows)
    except ComputeError as err:
        raise HTTPException(status_code=400, detail="Invalid csv file") from err
    else:
        return raw_panel


def parse_parquet(obj: str, n_rows: Optional[int] = None):
    try:
        raw_panel = pl.read_parquet(io.BytesIO(obj), n_rows=n_rows)
    except ArrowError as err:
        raise HTTPException(status_code=400, detail="Invalid parquet file") from err
    else:
        return raw_panel
