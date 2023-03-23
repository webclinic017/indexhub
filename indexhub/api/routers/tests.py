import json

from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/test/sources/ws")
async def ws_get_sources(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        if "user_id" in data:
            f = open("tests/snapshots/sources.json")
            response = json.load(f)
        else:
            response = {"error": "User id not provided"}
        await websocket.send_text(json.dumps(response, default=str))
