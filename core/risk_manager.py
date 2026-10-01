from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from core.client import invest_client
from core.config import settings


@dataclass
class RiskCheckResult:
    """Результат проверки риска"""
    allowed: bool
    reason: str = ""


class RiskManager:
    """
    Центральный модуль управления рисками.
    Все агенты обязаны проверять сделки через него перед выставлением ордера.
    """

    def __init__(self):
        self.max_position_size_percent = settings.MAX_POSITION_SIZE_PERCENT
        self.max_daily_loss_percent = settings.MAX_DAILY_LOSS_PERCENT
        self.max_drawdown_percent = settings.MAX_DRAWDOWN_PERCENT
        self.max_open_positions = settings.MAX_OPEN_POSITIONS
        self.max_order_value_rub = settings.MAX_ORDER_VALUE_RUB

    def get_portfolio_value(self) -> float:
        """Текущая стоимость портфеля в рублях"""
        with invest_client.get_client() as client:
            portfolio = client.operations.get_portfolio(
                account_id=invest_client.get_account_id()
            )
            # total_amount_portfolio уже в MoneyValue
            total = portfolio.total_amount_portfolio
            return float(total.units) + float(total.nano) / 1e9

    def get_open_positions_count(self) -> int:
        """Количество открытых позиций (бумаг)"""
        with invest_client.get_client() as client:
            positions = client.operations.get_positions(
                account_id=invest_client.get_account_id()
            )
            # Считаем только бумаги с ненулевым балансом
            count = 0
            for sec in positions.securities:
                if sec.balance != 0:
                    count += 1
            return count

    def check_order(
        self,
        order_value_rub: float,
        is_new_position: bool = True,
    ) -> RiskCheckResult:
        """
        Главная проверка перед выставлением ордера.
        
        :param order_value_rub: Сумма ордера в рублях
        :param is_new_position: True, если это открытие новой позиции (а не увеличение существующей)
        """
        # 1. Проверка максимальной суммы одной заявки
        if order_value_rub > self.max_order_value_rub:
            return RiskCheckResult(
                allowed=False,
                reason=f"Сумма ордера {order_value_rub:.0f} ₽ превышает лимит {self.max_order_value_rub:.0f} ₽"
            )

        portfolio_value = self.get_portfolio_value()

        if portfolio_value <= 0:
            return RiskCheckResult(
                allowed=False,
                reason="Стоимость портфеля равна нулю или отрицательная"
            )

        # 2. Проверка максимального размера позиции (% от портфеля)
        position_percent = (order_value_rub / portfolio_value) * 100
        if position_percent > self.max_position_size_percent:
            return RiskCheckResult(
                allowed=False,
                reason=(
                    f"Размер позиции {position_percent:.1f}% превышает "
                    f"лимит {self.max_position_size_percent}%"
                )
            )

        # 3. Проверка количества открытых позиций
        if is_new_position:
            open_count = self.get_open_positions_count()
            if open_count >= self.max_open_positions:
                return RiskCheckResult(
                    allowed=False,
                    reason=(
                        f"Уже открыто {open_count} позиций. "
                        f"Лимит: {self.max_open_positions}"
                    )
                )

        # TODO: позже добавим проверку дневного убытка и просадки
        # (для этого нужно будет хранить историю equity)

        return RiskCheckResult(allowed=True, reason="OK")

    def can_open_position(self, order_value_rub: float) -> RiskCheckResult:
        """Удобный метод специально для открытия новой позиции"""
        return self.check_order(order_value_rub=order_value_rub, is_new_position=True)


# Глобальный экземпляр
risk_manager = RiskManager()