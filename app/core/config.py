from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    POSTGRES_DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Cognito
    COGNITO_CLIENT_ID: str
    COGNITO_CLIENT_SECRET: str

    # AWS
    REGION_NAME: str
    # AWS_ACCESS_KEY_ID: str
    # AWS_SECRET_ACCESS_KEY: str

    # S3
    S3_RAW_VIDEOS_BUCKET: str
    S3_PROCESSED_VIDEOS_BUCKET: str
    S3_VIDEO_THUMBNAILS_BUCKET: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int


settings = Settings()
