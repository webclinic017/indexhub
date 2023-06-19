from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from fastapi import Request, WebSocket

from .auth0 import VerifyToken

class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request = None, websocket: WebSocket = None):
        # Temporarily disable protection for websockets
        if request != None:
            return await super().__call__(request)

token_auth_scheme = CustomHTTPBearer()


async def verify_oauth_token(token: str = Depends(token_auth_scheme)):
    result = VerifyToken(token.credentials).verify()
    if result.get("status"): 
        raise HTTPException(status_code=403, detail="Authentication failed")

