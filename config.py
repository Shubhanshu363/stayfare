import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///stayfare.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    APP_NAME = os.getenv("APP_NAME", "Stayfare")
    ENVIRONMENT = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "False").lower() in {"1", "true", "yes", "on"}
    TESTING = False
    PROVIDER_MODE = os.getenv("PROVIDER_MODE", "DEMO").upper()
    PROVIDER_TIMEOUT_SECONDS = int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "5"))
    PROVIDER_RETRY_ATTEMPTS = int(os.getenv("PROVIDER_RETRY_ATTEMPTS", "1"))
    RESTAURANT_PROVIDER_MODE = os.getenv("RESTAURANT_PROVIDER_MODE", "DEMO").upper()
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "False").lower() in {"1", "true", "yes", "on"}


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite://")


class ProductionConfig(Config):
    DEBUG = False
