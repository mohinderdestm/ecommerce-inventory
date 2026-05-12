from dotenv import load_dotenv
import os

load_dotenv()


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes")


def _parse_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _parse_int_map(value: str | None) -> dict[str, int]:
    parsed: dict[str, int] = {}
    if not value:
        return parsed

    for part in value.split(","):
        key, separator, raw_number = part.strip().partition("=")
        if not separator or not key.strip():
            continue
        try:
            parsed[key.strip()] = int(raw_number.strip())
        except ValueError:
            continue
    return parsed


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Inventory System")

    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "inventory_db")

    KAFKA_ENABLED: bool = _parse_bool(os.getenv("KAFKA_ENABLED"), False)
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
    )
    KAFKA_CLIENT_ID: str = os.getenv("KAFKA_CLIENT_ID", "inventory-service")
    KAFKA_GROUP_ID: str = os.getenv("KAFKA_GROUP_ID", "inventory-service")
    KAFKA_TOPIC_PREFIX: str = os.getenv("KAFKA_TOPIC_PREFIX", "inventory")
    KAFKA_AUTO_OFFSET_RESET: str = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")
    KAFKA_AUTO_CREATE_TOPICS: bool = _parse_bool(
        os.getenv("KAFKA_AUTO_CREATE_TOPICS"), True
    )
    KAFKA_DEFAULT_TOPIC_PARTITIONS: int = _parse_int(
        os.getenv("KAFKA_DEFAULT_TOPIC_PARTITIONS"), 3
    )
    KAFKA_DEFAULT_TOPIC_REPLICATION_FACTOR: int = _parse_int(
        os.getenv("KAFKA_DEFAULT_TOPIC_REPLICATION_FACTOR"), 1
    )
    KAFKA_TOPIC_PARTITIONS: dict[str, int] = _parse_int_map(
        os.getenv("KAFKA_TOPIC_PARTITIONS")
    )
    KAFKA_TOPIC_REPLICATION_FACTORS: dict[str, int] = _parse_int_map(
        os.getenv("KAFKA_TOPIC_REPLICATION_FACTORS")
    )

    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _parse_int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"), 60
    )

    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = _parse_int(os.getenv("SMTP_PORT"), 587)
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_SENDER_EMAIL: str = os.getenv("SMTP_SENDER_EMAIL", "")
    SMTP_SENDER_NAME: str = os.getenv("SMTP_SENDER_NAME", "Smart Inventory")
    SMTP_USE_TLS: bool = _parse_bool(os.getenv("SMTP_USE_TLS"), True)


settings = Settings()
