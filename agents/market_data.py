from t_tech.invest import InstrumentIdType

from agents.base_agent import BaseAgent
from core.client import invest_client


def _money_to_float(value) -> float:
    if value is None:
        return 0.0
    return float(value.units) + float(value.nano) / 1_000_000_000


class MarketDataAgent(BaseAgent):
    """Агент рыночных данных: цена и статус торгов по тикеру."""

    def get_share_by_ticker(self, ticker: str):
        ticker = ticker.upper().strip()

        with invest_client.get_client() as client:
            shares = client.instruments.shares().instruments
            for share in shares:
                if share.ticker == ticker and share.class_code == "TQBR":
                    return share
        return None

    def get_last_price(self, figi: str) -> float:
        with invest_client.get_client() as client:
            prices = client.market_data.get_last_prices(figi=[figi])
            if not prices.last_prices:
                return 0.0
            return _money_to_float(prices.last_prices[0].price)

    def get_trading_status(self, figi: str) -> str:
        with invest_client.get_client() as client:
            status = client.market_data.get_trading_status(figi=figi)
            return str(status.trading_status)

    def show_ticker(self, ticker: str):
        share = self.get_share_by_ticker(ticker)
        if share is None:
            print(f"Тикер {ticker} не найден")
            return

        price = self.get_last_price(share.figi)
        status = self.get_trading_status(share.figi)

        print(f"Тикер:     {share.ticker}")
        print(f"Название:  {share.name}")
        print(f"FIGI:      {share.figi}")
        print(f"Цена:      {price:.2f} ₽")
        print(f"Лот:       {share.lot}")
        print(f"Статус:    {status}")

    def run(self, ticker: str = "SBER"):
        print(f"\n=== {self.name} запущен ===\n")
        self.show_ticker(ticker)
        print("\n=== Агент завершил работу ===")