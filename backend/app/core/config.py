from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "JobMatch Cambodia API"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_USER: str = "jobmatch_user"
    POSTGRES_PASSWORD: str = "jobmatch_password"
    POSTGRES_DB: str = "jobmatch_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql://jobmatch_user:jobmatch_password@localhost:5432/jobmatch_db"
    
    # Security
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Scraper & Background Scheduler
    SCRAPER_INTERVAL_MINUTES: int = 30   # default: scrape every 30 minutes
    AUTO_SCRAPER_ENABLED: bool = True

    # Recommendation Engine
    WARM_EMBEDDINGS_ON_STARTUP: bool = False

    # Email & OTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_ENABLED: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
