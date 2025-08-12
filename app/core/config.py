from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "ToolCrib Backend"
    ENV: str = "dev"

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "12345678"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 2424
    POSTGRES_DB: str = "toolcrib"

    # Auth/Passwords
    DEFAULT_PASSWORD: str = "password"
    SECRET_KEY: str = "change-this-secret"
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    SESSION_DURATION_MINUTES: int = 60

    # Email
    EMAIL_FROM: str = "toolcribcmti@gmail.com"
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "smtp-user"
    SMTP_PASSWORD: str = "smtp-pass"
    SMTP_TLS: bool = True

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    def db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
