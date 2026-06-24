import os


class Settings:
    DATABASE_URL: str = os.environ["DATABASE_URL"]
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "changeme")
    JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")


settings = Settings()   