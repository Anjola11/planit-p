from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str
    BREVO_API_KEY:str
    BREVO_EMAIL: str
    model_config =SettingsConfigDict(
        env_file=".env",
        extra= 'ignore'
    )


Config = Settings()