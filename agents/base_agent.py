from core.portfolio import get_portfolio
from core.order_manager import place_market_order, close_position


class BaseAgent:
    """Базовый класс для всех торговых агентов."""

    def __init__(self, name: str):
        self.name = name

    def get_portfolio(self):
        return get_portfolio()

    def close(self, ticker: str):
        print(f"[{self.name}] Закрываю {ticker}...")
        return close_position(ticker)

    def buy(self, figi: str, quantity: int, order_value_rub: float):
        print(f"[{self.name}] Покупаю {quantity} лот. figi={figi}")
        return place_market_order(
            figi=figi,
            quantity=quantity,
            direction="buy",
            order_value_rub=order_value_rub,
        )

    def sell(self, figi: str, quantity: int, order_value_rub: float):
        print(f"[{self.name}] Продаю {quantity} лот. figi={figi}")
        return place_market_order(
            figi=figi,
            quantity=quantity,
            direction="sell",
            order_value_rub=order_value_rub,
        )

    def run(self):
        """Каждый агент реализует свою логику здесь."""
        raise NotImplementedError("Агент должен реализовать метод run()")