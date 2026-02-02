"""Configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Database
    database_path: str = "./data/wikidata.db"

    # Wikidata dump
    dump_path: str = "./data/dump.json.bz2"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Wikidata API (fallback for cache misses)
    wikidata_api: str = "https://www.wikidata.org/w/api.php"
    cache_ttl_days: int = 365

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
