"""Defines the IndexHub FastAPI app.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from indexhub.api.routers import trends, users, objectives, sources, readers, charts, tables, stats, tests, plans, integrations, inventory, router, unprotected_router

from .db import create_db_tables

# Health check
@unprotected_router.get("/", status_code=200)
def root():
    return {"message": "✅"}


app = FastAPI()
app.include_router(unprotected_router)
app.include_router(router)


origins = [
    "http://localhost:3000",
    "https://indexhub.vercel.app",
    "https://app.indexhub.ai",
    "https://api.indexhub.ai",
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
