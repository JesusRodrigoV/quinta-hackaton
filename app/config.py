from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field


class Settings(BaseSettings):
    APP_NAME: str = "Mobility Hub Service"
    ENV: str = "development"

    MONGO_URI: str = Field("mongodb://mongo:27017", env="MONGO_URI")
    MONGO_DB: str = Field("mobility_hub", env="MONGO_DB")

    KAFKA_BOOTSTRAP_SERVERS: str = Field("kafka:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_CLIENT_ID: str = Field("mobility-hub-service", env="KAFKA_CLIENT_ID")

    APSCHEDULER_TIMEZONE: str = "UTC"

    class Config:
        env_file = ".env"


settings = Settings()
