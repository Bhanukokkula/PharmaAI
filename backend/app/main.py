"""FastAPI entrypoint.

OTC / wellness products only. This API serves product information and
shopping flows — not medical advice. See README for full scope framing.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routes import cart, catalog, orders, recommend, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="PharmaAI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router)
app.include_router(cart.router)
app.include_router(users.router)
app.include_router(orders.router)
app.include_router(recommend.router)


@app.get("/")
def root() -> dict:
    return {
        "name": "PharmaAI API",
        "status": "ok",
        "scope": "OTC/wellness product info & shopping — not medical advice",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
