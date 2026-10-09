from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from t_tech.invest import OrderDirection, OrderType, SecurityTradingStatus
from t_tech.invest.schemas import PostOrderResponse
from core.client import invest_client
from core.risk_manager import risk_manager
from core.portfolio import get_portfolio

@dataclass
class OrderResult:
    success: bool
    message: str
    order_id: Optional[str] = None
    trading_status: Optional[str] = None   # добавили поле для удобства


def place_market_order(
    figi: str,
    quantity: int,          # количество лотов
    direction: str,         # "buy" или "sell"
    order_value_rub: float  # примерная сумма ордера в рублях (для проверки риска)
) -> OrderResult:
    """
    Безопасное выставление рыночного ордера.
    1. Проверяет риски
    2. Проверяет торговый статус инструмента
    3. Выставляет ордер
    """
        # 1. Проверка рисков
    existing = None
    try:
        portfolio = get_portfolio()
        for pos in portfolio.positions:
            if pos.figi == figi and pos.quantity != 0:
                existing = pos
                break
    except Exception:
        existing = None

    # Новая позиция только если по этому FIGI сейчас ничего нет.
    is_new_position = existing is None
    risk_check = risk_manager.check_order(
        order_value_rub=order_value_rub,
        is_new_position=is_new_position
    )
    if not risk_check.allowed:
        return OrderResult(
            success=False,
            message=f"Ордер запрещён риск-менеджером: {risk_check.reason}"
        )

    # 2. Определяем направление
    if direction == "buy":
        order_direction = OrderDirection.ORDER_DIRECTION_BUY
    elif direction == "sell":
        order_direction = OrderDirection.ORDER_DIRECTION_SELL
    else:
        return OrderResult(
            success=False,
            message="direction должен быть 'buy' или 'sell'"
        )

    # 3. Проверяем торговый статус + выставляем ордер
    try:
        with invest_client.get_client() as client:
            # --- Проверка торгового статуса ---
            status_response = client.market_data.get_trading_status(figi=figi)

            trading_status = status_response.trading_status
            market_available = status_response.market_order_available_flag
            api_available = status_response.api_trade_available_flag

            status_name = SecurityTradingStatus(trading_status).name

            if not (market_available and api_available):
                return OrderResult(
                    success=False,
                    message=(
                        f"Инструмент недоступен для рыночной торговли. "
                        f"Статус: {status_name}, "
                        f"market_order_available={market_available}, "
                        f"api_trade_available={api_available}"
                    ),
                    trading_status=status_name
                )

            # --- Выставляем ордер ---
            response: PostOrderResponse = client.orders.post_order(
                figi=figi,
                quantity=quantity,
                direction=order_direction,
                account_id=invest_client.get_account_id(),
                order_type=OrderType.ORDER_TYPE_MARKET,
                order_id=str(uuid4()),  # обязательно уникальный ID
            )

            return OrderResult(
                success=True,
                message="Ордер успешно выставлен",
                order_id=response.order_id,
                trading_status=status_name
            )

    except Exception as e:
        error_msg = str(e)

        # Более понятное сообщение для самой частой ошибки
        if "30079" in error_msg or "not available for trading" in error_msg.lower():
            return OrderResult(
                success=False,
                message=f"Инструмент недоступен для торговли (код 30079): {error_msg}"
            )

        return OrderResult(
            success=False,
            message=f"Ошибка при выставлении ордера: {error_msg}"
        )
def place_sell_order(
    figi: str,
    quantity: int,
    order_value_rub: float
) -> OrderResult:
    """
    Безопасная продажа (закрытие длинной позиции или открытие шорта).
    """
    return place_market_order(
        figi=figi,
        quantity=quantity,
        direction="sell",
        order_value_rub=order_value_rub
    )
def close_position(ticker: str) -> OrderResult:
    """
    Закрывает позицию по тикеру (например, 'SBER').
    Сама находит позицию, количество и направление.
    """
    ticker = ticker.upper().strip()
    portfolio = get_portfolio()

    position = None
    for pos in portfolio.positions:
        if pos.ticker.upper() == ticker or pos.figi == ticker:
            position = pos
            break

    if position is None:
        return OrderResult(
            success=False,
            message=f"Позиция {ticker} не найдена в портфеле"
        )

    quantity = abs(int(position.quantity))
    if quantity == 0:
        return OrderResult(
            success=False,
            message=f"По позиции {ticker} нулевое количество"
        )

    # Если quantity > 0 — длинная позиция, нужно продать
    # Если quantity < 0 — шорт, нужно купить (закрыть шорт)
    if position.quantity > 0:
        direction = "sell"
    else:
        direction = "buy"

    order_value = abs(position.value)

    print(f"Закрываем {ticker}: {quantity} лот., направление={direction}")

    return place_market_order(
        figi=position.figi,
        quantity=quantity,
        direction=direction,
        order_value_rub=order_value
    )