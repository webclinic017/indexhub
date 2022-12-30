import polars as pl


def _preproc(y_true: pl.LazyFrame, y_pred: pl.LazyFrame):
    # Coerce columnn names
    cols = y_true.columns
    y_pred = y_pred.rename({x: y for x, y in zip(y_pred.columns, cols)})
    # Coerce dtypes
    dtypes = y_true.dtypes
    y_pred = y_pred.select([pl.col(col).cast(dtypes[i]) for i, col in enumerate(cols)])

    return y_true, y_pred


def _score(y_true, y_pred, formula: pl.Expr, alias: str):
    y_true = y_true.rename({y_true.columns[-1]: "actual"})
    y_pred = y_pred.rename({y_pred.columns[-1]: "pred"})
    entity_col, time_col = y_true.columns[:2]
    scores = (
        y_true.join(y_pred, on=[entity_col, time_col])
        .groupby(entity_col)
        .agg(formula.alias(alias))
    )
    return scores


def mad(y_true: pl.LazyFrame, y_pred: pl.LazyFrame, suffix: str):
    y_true, y_pred = _preproc(y_true, y_pred)
    mad = (pl.col("actual") - pl.col("pred")).abs()
    return _score(y_true, y_pred, mad.mean(), f"mad:{suffix}")


def smape(y_true: pl.LazyFrame, y_pred: pl.LazyFrame, suffix: str):
    y_true, y_pred = _preproc(y_true, y_pred)

    # Reference: https://www.statology.org/smape-python/
    # 1/len(a) * np.sum(2 * np.abs(f-a) / (np.abs(a) + np.abs(f))*100)
    diff = (pl.col("pred") - pl.col("actual")).abs()
    total = pl.col("pred").abs() + pl.col("actual").abs()
    pct_error = 2 * diff / total
    return _score(y_true, y_pred, pct_error.mean() * 100, f"smape:{suffix}")
