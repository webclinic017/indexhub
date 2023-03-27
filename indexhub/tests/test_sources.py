import json

from fastapi.testclient import TestClient
from indexhub.api.server import app

client = TestClient(app)


def test_source_present(snapshot):
    response = client.get("/sources?user_id=test_auth0_id")
    snapshot.snapshot_dir = "frontend/tests/snapshots/sources"
    snapshot.assert_match(json.dumps(response.json()), "sources_list.json")
