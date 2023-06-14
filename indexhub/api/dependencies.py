from fastapi import Depends
from fastapi.security import HTTPBearer
from fastapi import Request, WebSocket
from jwt import exceptions

from .auth0 import VerifyToken

class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request = None, websocket: WebSocket = None):
        return await super().__call__(request or websocket)

token_auth_scheme = CustomHTTPBearer()


async def verify_oauth_token(token: str = Depends(token_auth_scheme)):
    try:
        _ = VerifyToken(token).verify()
    except exceptions.InvalidTokenError:
        raise
