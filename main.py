"""Головний модуль точки входу застосунку Contacts API.

Налаштовує життєвий цикл FastAPI, підключення до Redis,
ініціалізацію FastAPILimiter, CORS та підключення маршрутів API.
"""

from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter  # type: ignore

from src.api import auth, contacts, users
from src.conf.config import settings
from src.database.cache import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Керує запуском і зупинкою сервісів застосунку.

    На старті ініціалізує асинхронне з'єднання Redis для FastAPILimiter.
    Під час вимкнення коректно закриває з'єднання з Redis.
    """

    # 1. Ініціалізація асинхронного клієнта для FastAPILimiter
    redis_connection = redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(redis_connection)
    yield
    await redis_connection.close()
    redis_client.close()

app = FastAPI(title="Contacts API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
