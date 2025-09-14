from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/contacts_db_hw12"
    SECRET_KEY: str = "dev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Cache
    REDIS_URL: str = "redis://redis:6379/0"

    # SMTP (dev → MailHog)
    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@example.com"

    # Cloudinary
    CLOUDINARY_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
