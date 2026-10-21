from dataclasses import dataclass
from typing import List, Dict
from core.config import settings


@dataclass
class RiskRule:
    """Модели рисков по rules.txt"""
    capital_rub: int = 5000
    max_positions: int = 7
    max_lot_cost: int = 1000
    stop_loss_percent: float = -0.01
    profit_threshold_for_sell: float = 0.01
    max_buys_per_scan: int = 3


class RiskModels:
    """Центральные модели рисков и правил торговли (приоритет #1)"""
    def __init__(self):
        self.rules = RiskRule()

    def check_capital(self, current_capital: float) -> bool:
        """Проверка стартового капитала 5000₽"""
        return current_capital >= self.rules.capital_rub

    def get_max_positions(self) -> int:
        return self.rules.max_positions

    def classify_basket(self, lot_cost: float) -> str:
        """Корзины по стоимости лота"""
        if lot_cost < 100:
            return "CHE"
        elif lot_cost < 500:
            return "AVE"
        return "EXP"

    def is_sell_allowed_after_profit(self, profit_percent: float) -> bool:
        """SMA-sell только после +1%"""
        return profit_percent >= self.rules.profit_threshold_for_sell

    def should_stop_loss(self, drop_percent: float) -> bool:
        """-1% stop"""
        return drop_percent <= self.rules.stop_loss_percent

    def can_buy_scan(self, positions_count: int) -> bool:
        """Сканировать покупки только если ≤4 позиций"""
        return positions_count <= 4


risk_models = RiskModels()
