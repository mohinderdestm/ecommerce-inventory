from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Get absolute path to project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore"
    )

settings = Settings()