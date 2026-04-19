from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


SERVER_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=SERVER_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "智摄"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-this-secret-key"
    session_cookie_name: str = "photography_session"
    default_username: str = "admin"
    default_password: str = "change-this-password"
    default_display_name: str = "智摄管理员"
    storage_root: Path = Field(default_factory=lambda: SERVER_DIR / "storage")
    logs_root: Path = Field(default_factory=lambda: SERVER_DIR / "logs")
    knowledge_root: Path = Field(default_factory=lambda: SERVER_DIR / "knowledge")
    max_package_upload_mb: int = 150
    database_url: str | None = None
    default_reference_template: str = "reference_default"
    default_improve_template: str = "improve_default"
    app_base_url: str = "http://127.0.0.1:8000"
    time_zone: str = "Asia/Shanghai"

    @property
    def sqlite_dir(self) -> Path:
        return self.storage_root / "sqlite"

    @property
    def tasks_dir(self) -> Path:
        return self.storage_root / "tasks"

    @property
    def exports_dir(self) -> Path:
        return self.storage_root / "exports"

    @property
    def database_url_resolved(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{(self.sqlite_dir / 'photography.db').resolve().as_posix()}"

    def ensure_runtime_dirs(self) -> None:
        for path in (
            self.storage_root,
            self.logs_root,
            self.knowledge_root,
            self.sqlite_dir,
            self.tasks_dir,
            self.exports_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_runtime_dirs()
    return settings
