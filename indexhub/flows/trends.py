from functools import partial
import modal

from indexhub.api.demos import DEMO_SCHEMAS, DEMO_BUCKET
from indexhub.api.services.io import SOURCE_TAG_TO_READER

image = modal.Image.from_name("indexhub-image")
stub = modal.Stub(image=image)


@stub.function(
    memory=5120,
    cpu=4.0,
    secrets=[
        modal.Secret.from_name("aws-credentials"),
    ],
)
def upload_public_trends_metadata():
    import json
    import boto3

    read = partial(
        SOURCE_TAG_TO_READER["s3"],
        bucket_name=DEMO_BUCKET,
        file_ext="parquet",
    )

    s3_client = boto3.client("s3")

    for dataset_id, schema in DEMO_SCHEMAS.items():
        # Read metadata from schema
        path = schema["y"]
        entity_col = schema["entity_col"]
        metadata_path = schema["metadata"]
        df = read(object_path=path)
        entities = df[entity_col].unique().to_list()
        entity_count = df[entity_col].n_unique()
        metadata = {
            "dataset_id": dataset_id,
            "entities": entities,
            "entity_count": entity_count,
        }
        s3_client.put_object(
            Body=json.dumps(metadata), Bucket=DEMO_BUCKET, Key=metadata_path
        )


@stub.local_entrypoint()
def test():
    upload_public_trends_metadata.call()
