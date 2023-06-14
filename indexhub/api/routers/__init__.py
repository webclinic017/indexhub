from fastapi import APIRouter, Depends

from indexhub.api.dependencies import verify_oauth_token

# router = APIRouter(dependencies=[Depends(verify_oauth_token)])
router = APIRouter()

