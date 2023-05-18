"""Defines the IndexHub FastAPI app.
"""

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import create_db_and_tables
from .dependencies import verify_oauth_token
from .routers import (
    charts,
    copilot,
    integrations,
    objectives,
    plans,
    readers,
    sources,
    stats,
    tables,
    tests,
    users,
)


router = APIRouter()

# Health check
@router.get("/", status_code=200)
def health_check():
    return True


dependencies = [Depends(verify_oauth_token)]
app = FastAPI(dependencies=dependencies)

app.include_router(router)
app.include_router(users.router)
app.include_router(objectives.router)
app.include_router(sources.router)
app.include_router(readers.router)
app.include_router(charts.router)
app.include_router(tables.router)
app.include_router(stats.router)
app.include_router(tests.router)
app.include_router(plans.router)
app.include_router(copilot.router)
app.include_router(integrations.router)


origins = ["http://localhost:3000", "https://indexhub.vercel.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
