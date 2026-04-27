from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Inventory System")

    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "inventory_db")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_SENDER_EMAIL: str = os.getenv("SMTP_SENDER_EMAIL", "")
    SMTP_SENDER_NAME: str = os.getenv("SMTP_SENDER_NAME", "Smart Inventory")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in (
        "true",
        "1",
        "yes",
    )


settings = Settings()
