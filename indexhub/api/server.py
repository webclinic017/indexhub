"""Defines the IndexHub FastAPI app.
"""
import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import verify_oauth_token
from .routers import charts, data_tables, reports, sources, users
from .utils.init_db import create_db_and_tables

dependencies = None

if (os.getenv("DEBUG", "true").lower()) == "false":
    dependencies = [Depends(verify_oauth_token)]

app = FastAPI(dependencies=dependencies)

app.include_router(users.router)
app.include_router(reports.router)
app.include_router(charts.router)
app.include_router(data_tables.router)
app.include_router(sources.router)

origins = [
    "http://localhost",
    "http://localhost:3000",
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
    create_db_and_tables()
