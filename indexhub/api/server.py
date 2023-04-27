"""Defines the IndexHub FastAPI app.
"""
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import create_db_and_tables
from .dependencies import verify_oauth_token
from .routers import policies, readers, sources, users, charts, tables, tests, stats, plans

dependencies = None

if (os.getenv("DEBUG", "true").lower()) == "false":
    dependencies = [Depends(verify_oauth_token)]

app = FastAPI(dependencies=dependencies)

app.include_router(users.router)
app.include_router(policies.router)
app.include_router(sources.router)
app.include_router(readers.router)
app.include_router(charts.router)
app.include_router(tables.router)
app.include_router(stats.router)
app.include_router(tests.router)
app.include_router(plans.router)


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
