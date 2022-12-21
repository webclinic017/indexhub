from fastapi import Depends
from fastapi.security import HTTPBearer
from jwt import exceptions

from .utils.auth0 import VerifyToken

token_auth_scheme = HTTPBearer()


async def verify_oauth_token(token: str = Depends(token_auth_scheme)):
    try:
        _ = VerifyToken(token).verify()
    except exceptions.InvalidTokenError:
        raise
