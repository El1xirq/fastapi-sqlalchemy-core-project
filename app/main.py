from fastapi import FastAPI
from app.routers import users, orders, products
from .database import engine, metadata
from contextlib import asynccontextmanager
from . import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(users.router)
app.include_router(orders.router)
app.include_router(products.router)