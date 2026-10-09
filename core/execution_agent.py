from dataclasses import dataclass
from typing import Optional, Literal
from uuid import uuid4

from core.order_manager import place_market_order, OrderResult
from core.portfolio import get_portfolio
from core.risk_manager import risk_manager


ActionType = Literal["buy", "sell"]


@dataclass
class TradeSignal:
    action: ActionType
    figi: str
    quantity: int
    order_value_rub: float
    reason: str = ""
    signal_id: Optional[str] = None
    ticker: str = ""


@dataclass
class ExecutionResult:
    success: bool
    message: str
    order_id: Optional[str] = None
    signal_id: Optional[str] = None
    trading_status: Optional[str] = None
    portfolio_after: Optional[dict] = None
    skipped: bool = False


class ExecutionAgent:
    def __init__(self, auto_execute: bool = False):
        self.name = "ExecutionAgent"
        self.auto_execute = auto_execute  # False = только логируем, ордер не ставим

    def _find_position(self, figi: str):
        portfolio = get_portfolio()
        for pos in portfolio.positions:
            if pos.figi == figi:
                return pos, portfolio
        return None, portfolio

    def execute(self, signal: TradeSignal) -> ExecutionResult:
        if signal.signal_id is None:
            signal.signal_id = str(uuid4())

        label = signal.ticker or signal.figi
        print(f"[{self.name}] Сигнал: {signal.action.upper()} "
              f"{signal.quantity} лот(ов) {label}")
        if signal.reason:
            print(f"[{self.name}] Причина: {signal.reason}")

        try:
            position, portfolio = self._find_position(signal.figi)
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Не удалось прочитать портфель: {e}",
                signal_id=signal.signal_id,
            )

        # --- Правила безопасности ---
        if signal.action == "sell":
            if position is None:
                return ExecutionResult(
                    success=False,
                    skipped=True,
                    message=f"SELL пропущен: нет позиции по {label}",
                    signal_id=signal.signal_id,
                )
            if position.quantity < signal.quantity:
                return ExecutionResult(
                    success=False,
                    skipped=True,
                    message=(
                        f"SELL пропущен: в портфеле {position.quantity} шт., "
                        f"а сигнал просит {signal.quantity}"
                    ),
                    signal_id=signal.signal_id,
                )

                qty = 0
        if position is not None:
            qty = int(position.quantity)

        if signal.action == "sell":
            if qty <= 0:
                return ExecutionResult(
                    success=False,
                    skipped=True,
                    message=f"SELL пропущен: нет длинной позиции по {label} (qty={qty})",
                    signal_id=signal.signal_id,
                )
            if qty < signal.quantity:
                return ExecutionResult(
                    success=False,
                    skipped=True,
                    message=(
                        f"SELL пропущен: в портфеле {qty} шт., "
                        f"а сигнал просит {signal.quantity}"
                    ),
                    signal_id=signal.signal_id,
                )

        if signal.action == "buy":
            if qty > 0:
                return ExecutionResult(
                    success=False,
                    skipped=True,
                    message=f"BUY пропущен: лонг по {label} уже открыт ({qty} шт.)",
                    signal_id=signal.signal_id,
                )
            if qty == 0 and signal.order_value_rub >= 1000:
                return ExecutionResult(
                    success=False,
                    skipped=True,
                    message=f"BUY пропущен: цена/лот ~{signal.order_value_rub:.2f} ₽ >= 1000 ₽",
                    signal_id=signal.signal_id,
                )

        # Режим наблюдения: сигнал есть, ордер не ставим
        if not self.auto_execute:
            return ExecutionResult(
                success=True,
                skipped=True,
                message=f"Сигнал принят, но auto_execute=False — ордер не выставлен",
                signal_id=signal.signal_id,
            )

        order_result: OrderResult = place_market_order(
            figi=signal.figi,
            quantity=signal.quantity,
            direction=signal.action,
            order_value_rub=signal.order_value_rub,
        )

        if not order_result.success:
            return ExecutionResult(
                success=False,
                message=order_result.message,
                signal_id=signal.signal_id,
                trading_status=getattr(order_result, "trading_status", None),
            )

        try:
            portfolio = get_portfolio()
            portfolio_snapshot = {
                "total_value": portfolio.total_value,
                "free_cash": portfolio.free_cash,
                "positions_count": len(portfolio.positions),
                "positions": [
                    {
                        "figi": p.figi,
                        "name": p.name,
                        "quantity": p.quantity,
                        "current_price": p.current_price,
                        "value": p.value,
                    }
                    for p in portfolio.positions
                ],
            }
        except Exception as e:
            portfolio_snapshot = {"error": str(e)}

        return ExecutionResult(
            success=True,
            message=f"Ордер исполнен: {signal.action} {signal.quantity} лот(ов) {label}",
            order_id=order_result.order_id,
            signal_id=signal.signal_id,
            trading_status=getattr(order_result, "trading_status", None),
            portfolio_after=portfolio_snapshot,
        )


# По умолчанию НЕ торгуем автоматически
execution_agent = ExecutionAgent(auto_execute=False)