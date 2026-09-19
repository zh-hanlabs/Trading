from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "A股专业投研智能体系统"
    APP_ENV: str = "development"
    APP_PORT: int = 8000

    # PostgreSQL 配置 (直连本地/远程 Docker 数据库)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "trading_user"
    POSTGRES_PASSWORD: str = "trading_password"
    POSTGRES_DB: str = "trading"

    # 时区配置
    TZ: str = "Asia/Shanghai"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
