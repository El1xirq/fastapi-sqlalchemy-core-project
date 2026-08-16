from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import MetaData
from .settings_app import settings
from contextlib import asynccontextmanager



engine = create_async_engine(settings.DATABASE_URL)
metadata = MetaData(schema='public')


@asynccontextmanager
async def get_connection():
    """Асинхронно предоставляет подключение к базе данных."""
    async with engine.begin() as connection:
        yield connection
        