"""Defines the IndexHub FastAPI app.
"""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from indexhub.api.routers import trends

from .db import create_db_tables
from .routers import (
    charts,
    integrations,
    inventory,
    objectives,
    plans,
    readers,
    sources,
    stats,
    tables,
    tests,
    trends,
    users,
)


router = APIRouter()

# Health check
@router.get("/", status_code=200)
def root():
    return {"message": "✅"}


app = FastAPI()
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
app.include_router(integrations.router)
app.include_router(trends.router)
app.include_router(inventory.router)


origins = [
    "http://localhost:3000",
    "https://indexhub.vercel.app",
    "https://app.indexhub.ai",
    "https://api_v2.indexhub.ai",  # https://api.indexhub.ai
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_tables()
