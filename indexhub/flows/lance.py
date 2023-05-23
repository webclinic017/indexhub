from typing import List
import modal


image = modal.Image.debian_slim().pip_install("pylance", "polars")
stub = modal.Stub(name="indexhub-io", image=image)


@stub.function(
    memory=5120,
    cpu=4.0,
    secrets=[
        modal.Secret.from_name("aws-credentials"),
    ]
)
def read_lance_dataset(uri: str, columns: List[str] = None, n_rows: int = 1000):
    import lance
    import polars as pl
    ds = lance.dataset(uri)
    table = ds.to_table(limit=n_rows, columns=columns)
    df = pl.from_arrow(table)
    return df