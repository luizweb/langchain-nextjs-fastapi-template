from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', extra='ignore'
    )

    # Variáveis de ambiente
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    BASE_DIR: Path = Path(__file__).resolve().parent

    @property
    def templates_dir(self) -> Path:
        return self.BASE_DIR / "templates"

    @property
    def static_dir(self) -> Path:
        return self.BASE_DIR / "static"


settings = Settings()
