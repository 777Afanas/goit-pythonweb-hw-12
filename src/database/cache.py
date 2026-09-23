"""
Модуль для ініціалізації та конфігурації клієнта кешування Redis.
"""

import redis
from src.conf.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=False,
)
"""Екземпляр синхронного клієнта Redis для кешування користувачів та операцій додатку."""
