from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str

    # Cognito
    COGNITO_CLIENT_ID: str
    COGNITO_CLIENT_SECRET: str

    # AWS
    REGION_NAME: str


settings = Settings()
