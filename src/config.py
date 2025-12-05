"""Application configuration.

This module exposes a single `Config` instance which loads settings from
environment variables (and an optional `.env` file). Use the `Config`
object to access runtime configuration such as database DSNs and secret
keys. Keep secrets (like `JWT_KEY`) out of source control and provide
them via environment variables or a secrets manager in production.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from the environment.

    Declare settings as class attributes to get validation and helpful
    error messages when required values are missing. Keep the surface
    area minimal and prefer loading sensitive values from environment
    variables in production.
    """

    DATABASE_URL: str
    BREVO_API_KEY: str
    BREVO_EMAIL: str
    BREVO_SENDER_NAME: str
    JWT_KEY: str
    JWT_ALGORITHM: str

    # Tell pydantic-settings to read a local `.env` file during
    # development while ignoring extra environment variables.
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


# Single Settings instance used across the app.
Config = Settings()