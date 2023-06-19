import json

from fastapi import WebSocket

from indexhub.api.routers import unprotected_router


@unprotected_router.websocket("/test/sources/ws")
async def ws_get_sources(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        if "user_id" in data:
            f = open("frontend/tests/snapshots/sources/sources_list.json")
            response = json.load(f)
        else:
            response = {"error": "User id not provided"}
        await websocket.send_text(json.dumps(response, default=str))
