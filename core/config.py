from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === TBank Invest ===
    INVEST_TOKEN: str = Field(..., description="Токен TBank Invest API")
    ACCOUNT_ID: str = Field(..., description="ID счёта в песочнице или боевом режиме")
    MODE: Literal["sandbox", "production"] = "sandbox"

    # === Risk Management (самые важные лимиты) ===
    MAX_POSITION_SIZE_PERCENT: float = 10.0          # Макс. размер одной позиции (% от портфеля)
    MAX_DAILY_LOSS_PERCENT: float = 3.0              # Макс. дневной убыток (%)
    MAX_DRAWDOWN_PERCENT: float = 8.0                # Макс. просадка портфеля (%)
    MAX_OPEN_POSITIONS: int = 5                      # Макс. количество открытых позиций
    MAX_ORDER_VALUE_RUB: float = 50_000.0            # Макс. сумма одной заявки в рублях

    # === Trading ===
    DEFAULT_CURRENCY: str = "rub"
    COMMISSION_PERCENT: float = 0.05                 # Комиссия брокера (примерно)

    # === Logging & Monitoring ===
    LOG_LEVEL: str = "INFO"
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None

    # === Paths ===
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    LOGS_DIR: Path = BASE_DIR / "logs"
    DATA_DIR: Path = BASE_DIR / "data"

    def is_sandbox(self) -> bool:
        return self.MODE == "sandbox"


# Глобальный объект настроек (используется во всём проекте)
settings = Settings()