from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаются из переменных окружения / .env файла."""

    # Обязательные поля — приложение не запустится без них
    database_url: str
    secret_key: str

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    api_title: str = "RICEBoard API"
    api_version: str = "0.1.0"

    # extra="ignore" — игнорировать лишние переменные из .env (например POSTGRES_*)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# pylint: disable=no-value-for-parameter
settings = Settings()
