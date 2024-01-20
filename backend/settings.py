"""Файл с конфигами для подключенния бдэшки к нашей апи"""

from envparse import Env

env = Env()

REAL_DATABASE_URL = env.str(
    "REAL_DATABASE_URL",
    default = "postgresql+asyncpg://postgres:postgres@0.0.0.0:5432/postgres"
)   # конект string для бдэшки

TEST_DATABASE_URL = env.str(
    "TEST_DATABASE_URL",
    default = "postgresql+asyncpg://postgres_test:postgres_test@0.0.0.0:5433/postgres_test"
)   # конект string для бдэшки