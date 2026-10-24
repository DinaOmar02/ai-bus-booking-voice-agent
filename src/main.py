import asyncio
import logging

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.helpers.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

postgres_conn = URL.create(
    "postgresql+asyncpg",
    username=settings.POSTGRES_USERNAME,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    database=settings.POSTGRES_DB,
)
db_engine = create_async_engine(postgres_conn, pool_pre_ping=True)
session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
