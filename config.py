from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    url: str
    token: str
    theme: str = "light"
    is_grid: bool = True

    model_config = SettingsConfigDict(
        validate_default=False,
        env_prefix="GRAFANA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )