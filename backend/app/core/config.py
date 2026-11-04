from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from decimal import Decimal
import os
from pathlib import Path

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "KarigarFlow"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+psycopg2://postgres@localhost:5433/karigarflow_db"
    
    SECRET_KEY: str = "karigarflow-dev-insecure-secret-key-change-in-production-123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hour workshop shift

    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # Jewellery Workshop Gold Calculations Defaults (Decimals)
    DEFAULT_PURITY_PURCHASE: Decimal = Decimal("99.90")  # 24K pure bar
    DEFAULT_PURITY_ORNAMENT_22K: Decimal = Decimal("91.60")  # 22K 916 BIS Hallmark
    DEFAULT_PURITY_ORNAMENT_18K: Decimal = Decimal("75.00")  # 18K 750 BIS Hallmark
    MAX_ALLOWED_WASTAGE_PERCENT: Decimal = Decimal("2.50")
    LOSS_ALERT_THRESHOLD_GRAMS: Decimal = Decimal("0.100")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

