import json
import logging
import os
from datetime import datetime
from typing import Any, List, Literal, Mapping, Optional, Union

import boto3
import modal
import pandas as pd
import polars as pl
from botocore.exceptions import ClientError
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from sqlmodel import Session, select

from indexhub.api.db import create_sql_engine
from indexhub.api.models.source import Source
from indexhub.api.routers.users import get_user_by_id
from indexhub.api.schemas import (
    FREQ_TO_DURATION,
    SUPPORTED_DATETIME_FMT,
    SUPPORTED_FREQ,
)
from indexhub.api.services.io import (
    SOURCE_TAG_TO_READER,
    STORAGE_TAG_TO_WRITER,
    check_s3_path,
)
from indexhub.api.services.secrets_manager import get_aws_secret
from indexhub.modal_stub import stub


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

PL_FLOAT_DTYPES = [pl.Float32, pl.Float64]
PL_INT_DTYPES = [pl.Int8, pl.Int16, pl.Int32, pl.Int64]
PL_NUMERIC_COLS = pl.col([*PL_FLOAT_DTYPES, *PL_INT_DTYPES])


env_prefix = os.environ.get("ENV_NAME", "dev")


def _clean_panel(
    raw_panel_data: pl.DataFrame,
    entity_cols: List[str],
    time_col: str,
    datetime_fmt: str,
) -> pl.DataFrame:
    expr = [
        # Defensive replace #N/A generated by nulls/blanks to 0
        pl.col(entity_cols).str.replace("#N/A", "0"),
    ]
    if raw_panel_data.get_column(time_col).dtype not in [pl.Date, pl.Datetime]:
        if datetime_fmt.endswith("%H:%M"):
            dtype = pl.Datetime
        else:
            dtype = pl.Date

        expr.append(pl.col("time").cast(pl.Utf8).str.strptime(dtype, fmt=datetime_fmt))

    panel_data = (
        raw_panel_data.rename({time_col: "time"}).with_columns(expr)
        # Downcast dtypes
        .select(pl.all().shrink_dtype())
        # Sort by entity and time
        .sort(by=[*entity_cols, "time"])
    )
    return panel_data


def _merge_multilevels(
    X: pl.DataFrame,
    entity_cols: List[str],
    target_col: str,
) -> pl.DataFrame:
    entity_col = "__".join(entity_cols)
    X_new = (
        # Combine subset of entity columns
        X.lazy()
        .with_columns(
            pl.concat_str(entity_cols, separator=" - ")
            .cast(pl.Categorical)
            .alias(entity_col)
        )
        # Select and sort columns
        .select(
            [
                entity_col,
                "time",
                target_col,
                pl.exclude([entity_col, "time", target_col]),
            ]
        )
        .sort([entity_col, "time"])
        .with_columns([pl.col(entity_col).set_sorted(), pl.col("time").set_sorted()])
        .collect()
    )
    return X_new


def _reindex_panel(X: pl.LazyFrame, freq: str, sort: bool = False) -> pl.DataFrame:
    # Create new index
    entity_col = X.columns[0]
    time_col = X.columns[1]
    dtypes = X.dtypes[:2]

    with pl.StringCache():
        entities = X.collect().get_column(entity_col).unique().to_frame()
        dates = X.collect().get_column(time_col)
        timestamps = pl.date_range(dates.min(), dates.max(), interval=freq).to_frame(
            name=time_col
        )

        full_idx = entities.join(timestamps, how="cross")
        # Defensive cast dtypes to be consistent with df
        full_idx = full_idx.select(
            [pl.col(col).cast(dtypes[i]) for i, col in enumerate(full_idx.columns)]
        )

        # Outer join
        X_new = (
            # Must collect before join otherwise will hit error:
            # Joins/or comparisons on categorical dtypes can only happen if they are created under the same global string cache.
            X.collect().join(full_idx, on=[entity_col, time_col], how="outer")
        )

    if sort:
        X_new = X_new.sort([entity_col, time_col]).with_columns(
            [pl.col(entity_col).set_sorted(), pl.col(time_col).set_sorted()]
        )
    return X_new


def _impute(
    X: pl.DataFrame,
    method: Union[
        Literal["mean", "median", "fill", "ffill", "bfill", "interpolate"],
        Union[int, float],
    ],
) -> pl.DataFrame:
    entity_col = X.columns[0]
    method_to_expr = {
        "mean": PL_NUMERIC_COLS.fill_null(PL_NUMERIC_COLS.mean().over(entity_col)),
        "median": PL_NUMERIC_COLS.fill_null(PL_NUMERIC_COLS.median().over(entity_col)),
        "fill": [
            pl.col(PL_FLOAT_DTYPES).fill_null(
                pl.col(PL_FLOAT_DTYPES).mean().over(entity_col)
            ),
            pl.col(PL_INT_DTYPES).fill_null(
                pl.col(PL_INT_DTYPES).median().over(entity_col)
            ),
        ],
        "ffill": PL_NUMERIC_COLS.fill_null(strategy="forward").over(entity_col),
        "bfill": PL_NUMERIC_COLS.fill_null(strategy="backward").over(entity_col),
        "interpolate": PL_NUMERIC_COLS.interpolate().over(entity_col),
    }
    if isinstance(method, int) or isinstance(method, float):
        expr = PL_NUMERIC_COLS.fill_null(pl.lit(method))
    else:
        expr = method_to_expr[method]
    X_new = X.with_columns(expr)
    return X_new


def _resample_panel(
    X: pl.DataFrame,
    freq: str,
    target_col: str,
    agg_method: Optional[str] = "sum",
    impute_method: Optional[Union[str, int, float]] = 0,
    price_col: Optional[str] = None,
) -> pl.DataFrame:
    entity_col, time_col = X.columns[:2]
    # Agg target, numeric transaction cols, and numeric feature cols
    agg_cols = [*PL_FLOAT_DTYPES, *PL_INT_DTYPES]
    agg_to_expr = {
        "sum": pl.col(agg_cols).sum(),
        "mean": pl.col(agg_cols).mean(),
        "median": pl.col(agg_cols).median(),
    }

    # Transaction type
    if price_col is not None:
        agg_exprs = [
            # Fixed agg methods for quantity and price cols
            pl.col(target_col).sum(),
            pl.col(price_col).mean(),
            agg_to_expr[agg_method].exclude([target_col, price_col]),
        ]
    # Panel type
    else:
        agg_exprs = [agg_to_expr[agg_method]]

    X_new = (
        # Defensive resampling
        X.lazy()
        .groupby_dynamic(time_col, every=freq, by=entity_col)
        .agg(agg_exprs)
        # Must defensive sort columns otherwise time_col and target_col
        # positions are incorrectly swapped in lazy
        .select(
            [
                entity_col,
                time_col,
                target_col,
                pl.exclude([entity_col, time_col, target_col]),
            ]
        )
        # Reindex full (entity, time) index
        .pipe(_reindex_panel, freq=freq, sort=True)
        # Impute gaps after reindex
        .pipe(_impute, impute_method)
        # Defensive fill null with 0 for impute method `ffill`
        .fill_null(0)
    )
    return X_new


def _make_output_path(source_id: int, updated_at: datetime, prefix: str) -> str:
    timestamp = datetime.strftime(updated_at, "%Y%m%dT%X").replace(":", "")
    path = f"staging/{source_id}/{timestamp}.parquet"
    if prefix != "":
        path = f"{prefix}/{path}"
    return path


def _update_source(
    source_id: int,
    updated_at: datetime,
    output_path: Union[str, None],
    status: str,
    msg: str,
) -> Source:
    # Establish connection
    engine = create_sql_engine()
    with Session(engine) as session:
        # Select rows with specific report_id only
        query = select(Source).where(Source.id == source_id)
        source = session.exec(query).one()
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        # Update the fields based on the source_id
        source.updated_at = updated_at
        source.output_path = output_path
        source.status = status
        source.msg = msg
        # Add, commit and refresh the updated object
        session.add(source)
        session.commit()
        session.refresh(source)
        return source


def _embed_ts(panel_data: pl.DataFrame) -> pl.DataFrame:
    env_prefix = os.environ.get("ENV_NAME", "dev")
    ts_emb_flow = modal.Function.lookup(
        f"{env_prefix}-functime-flows", "embed_cluster_time_series"
    )
    # Unpack panel data cols based on source type
    entity_col = panel_data.columns[0]
    target_col = panel_data.columns[-1]
    # Generate embeddings for panel
    embs = ts_emb_flow.call(
        data=panel_data.to_arrow(), entity_col=entity_col, target_col=target_col
    )
    return embs


def _upload_embs(
    embs: pl.DataFrame,
    source_id: int,
    storage_bucket_name: str,
    prefix: str,
):
    import lance

    # Export embeddings as .lance
    uri = f"vectors/{source_id}.lance/"
    # Change to pandas df and write to .lance due to ValueError
    try:
        lance.write_dataset(embs.to_pandas(), uri, mode="overwrite")
    except OSError:
        lance.write_dataset(embs.to_pandas(), uri, mode="create")
    # Upload entire .lance directory to s3
    s3 = boto3.client("s3")
    for root, _, files in os.walk(uri):
        for file in files:
            file_path = os.path.join(root, file)
            if root[-1] != "/":
                key = prefix + "/" + root + "/" + file
            else:
                key = prefix + "/" + root + file
            s3.upload_file(file_path, storage_bucket_name, key)
    if prefix == "":
        path = f"s3://{storage_bucket_name}/{uri}"
    else:
        path = f"s3://{storage_bucket_name}/{prefix}/{uri}"
    return path


@stub.function()
def run_preprocess(
    user_id: int,
    source_id: int,
    source_tag: str,
    conn_fields: Mapping[str, Any],
    source_type: str,
    data_fields: Mapping[str, Any],
    storage_tag: str,
    storage_bucket_name: str,
):
    """Load panel dataset then clean, write, and compute time-series embeddings."""
    try:
        status, msg = "SUCCESS", "OK"
        object_path = conn_fields.get("object_path")
        if "/" in object_path:
            prefix = object_path.split("/")[0]
        else:
            prefix = ""

        # Get credentials
        source_creds = get_aws_secret(
            tag=source_tag, secret_type="sources", user_id=user_id
        )
        storage_creds = get_aws_secret(
            tag=storage_tag, secret_type="storage", user_id=user_id
        )
        dateformat = SUPPORTED_DATETIME_FMT[data_fields["datetime_fmt"]]
        if source_tag == "s3":
            path_type = check_s3_path(
                bucket_name=conn_fields["bucket_name"],
                object_path=object_path,
                **source_creds,
            )
            source_tag = f"{source_tag}{path_type}"
        # Read data from source
        read = SOURCE_TAG_TO_READER[source_tag]
        raw_panel_data = read(**conn_fields, **source_creds, dateformat=dateformat)
        # Set quantity as target if transaction type
        target_col = data_fields.get("target_col", data_fields.get("quantity_col"))
        entity_cols = data_fields.get("entity_cols", [])
        if source_type == "transaction":
            # Set product as entity if transaction type
            entity_cols = [data_fields["product_col"], *entity_cols]
        time_col = data_fields.get("time_col")
        idx_cols = [*entity_cols, time_col]

        if isinstance(raw_panel_data, List) and all(
            isinstance(df, pl.DataFrame) for df in raw_panel_data
        ):
            # Concat and drop duplicates based on time_col and entity_cols
            raw_panel_data = (
                pl.concat(raw_panel_data)
                .sort([*idx_cols, "upload_date"])
                .unique(
                    subset=idx_cols,
                    keep="last",
                )
                .select(pl.all().exclude("upload_date"))
            )
        panel_data = (
            raw_panel_data
            # Clean data
            .pipe(
                _clean_panel,
                entity_cols=entity_cols,
                time_col=time_col,
                datetime_fmt=dateformat,
            )
            # Merge multi levels
            .pipe(
                _merge_multilevels,
                entity_cols=entity_cols,
                target_col=target_col,
            )
            # Resample panel
            .pipe(
                _resample_panel,
                freq=SUPPORTED_FREQ[data_fields["freq"]],
                target_col=target_col,
                agg_method=data_fields.get("agg_method", "sum"),
                impute_method=data_fields.get("impute_method", 0),
                price_col=data_fields.get("price_col", None),
            )
        )
        # Write data to data lake storage
        updated_at = datetime.utcnow()
        write = STORAGE_TAG_TO_WRITER[storage_tag]
        output_path = _make_output_path(
            source_id=source_id, updated_at=updated_at, prefix=prefix
        )
        write(
            panel_data,
            bucket_name=storage_bucket_name,
            object_path=output_path,
            **storage_creds,
        )
        # TODO: Pending to fix issue in modal
        # Embed time series and write to S3
        # embs = _embed_ts(panel_data=panel_data)
        # _upload_embs(
        #     pl.from_arrow(embs),
        #     source_id=source_id,
        #     storage_bucket_name=storage_bucket_name,
        #     prefix=prefix,
        # )

    except ClientError as exc:
        status = "FAILED"
        panel_data = None
        output_path = None
        error_code = exc.response["Error"]["Code"]
        if error_code == "InvalidSignatureException":
            msg = "Authentication secret errors"
        elif error_code == "AccessDeniedException":
            msg = "Insufficient permissions errors"
        else:
            msg = repr(exc)
        logger.exception(exc)

    except HTTPException as exc:
        # Source file / table not found errors
        status = "FAILED"
        panel_data = None
        output_path = None
        msg = repr(exc)
        logger.exception(exc)

    except Exception as exc:
        status = "FAILED"
        panel_data = None
        output_path = None
        msg = repr(exc)
        logger.exception(exc)

    finally:
        # Update state in database
        _update_source(
            source_id=source_id,
            updated_at=datetime.utcnow(),
            output_path=output_path,
            status=status,
            msg=msg,
        )


@stub.function(
    memory=5120,
    cpu=4.0,
    timeout=900,
    schedule=modal.Cron("0 16 * * *"),  # run at 12am daily (utc 4pm)
)
def schedule_preprocess():
    # 1. Get all sources
    engine = create_sql_engine()
    with Session(engine) as session:
        query = select(Source)
        sources = session.exec(query).all()

    if sources:
        futures = []
        for source in sources:
            logger.info(f"Checking source: {source.id}")
            data_fields = json.loads(source.data_fields)
            # 2. Get user
            user = get_user_by_id(source.user_id)
            # 3. Check freq from source for schedule
            duration = FREQ_TO_DURATION[data_fields["freq"]]
            updated_at = source.updated_at.replace(microsecond=0)
            if duration == "1mo":
                new_dt = updated_at + relativedelta(months=1)
                run_dt = datetime(new_dt.year, new_dt.month, 1)
            elif duration == "3mo":
                new_dt = updated_at + relativedelta(months=3)
                run_dt = datetime(new_dt.year, new_dt.month, 1)
            else:
                run_dt = updated_at + pd.Timedelta(hours=int(duration[:-1]))
            logger.info(f"Next run for {source.id} at: {run_dt}")
            # 4. Run preprocess flow
            current_datetime = datetime.now().replace(microsecond=0)
            if (current_datetime >= run_dt) or source.status == "FAILED":
                # Spawn preprocess and embs flow for source
                futures.append(
                    run_preprocess.spawn(
                        user_id=source.user_id,
                        source_id=source.id,
                        source_tag=source.tag,
                        conn_fields=json.loads(source.conn_fields),
                        source_type=source.dataset_type,
                        data_fields=data_fields,
                        storage_tag=user.storage_tag,
                        storage_bucket_name=user.storage_bucket_name,
                    )
                )

        for future in futures:
            future.get()


@stub.local_entrypoint()
def test():
    user_id = os.environ["USER_ID"]

    # Source
    source_id = 1
    source_tag = "s3"
    conn_fields = {
        "bucket_name": "indexhub-demo-dev",
        "object_path": "raw/tourism/tourism_20221212.parquet",
        "file_ext": "parquet",
    }
    source_type = "panel"
    data_fields = {
        "entity_cols": ["state"],
        "time_col": "time",
        "target_col": "trips_in_000s",
        "feature_cols": [],
        "freq": "Monthly",
        "datetime_fmt": "Year-Month-Day",
    }

    # User
    storage_tag = "s3"
    storage_bucket_name = "indexhub-demo-dev"
    run_preprocess(
        user_id=user_id,
        source_id=source_id,
        source_tag=source_tag,
        conn_fields=conn_fields,
        source_type=source_type,
        data_fields=data_fields,
        storage_tag=storage_tag,
        storage_bucket_name=storage_bucket_name,
    )
