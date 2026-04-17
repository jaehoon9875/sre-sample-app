from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # CI 환경에서는 .env 파일이 없을 수 있어 기본값을 둔다.
    # 로컬/운영에서는 환경변수가 있으면 해당 값으로 자동 override 된다.
    DATABASE_URL: str = "postgresql+asyncpg://sre:sre_password@localhost:5432/orders"
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:29092"
    INVENTORY_SERVICE_URL: str = "http://localhost:8002"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
