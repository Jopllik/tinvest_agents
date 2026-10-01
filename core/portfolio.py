from dataclasses import dataclass
from typing import List

from t_tech.invest import InstrumentIdType

from core.client import invest_client


@dataclass
class Position:
    figi: str
    ticker: str
    name: str
    quantity: int          # количество лотов (может быть отрицательным при шорте)
    average_price: float   # средняя цена
    current_price: float   # текущая цена
    value: float           # текущая стоимость позиции


@dataclass
class PortfolioInfo:
    total_value: float           # вся стоимость портфеля
    free_cash: float             # свободные деньги в рублях
    positions: List[Position]    # список открытых позиций


def _money_to_float(money) -> float:
    """Переводит MoneyValue / Quotation в обычное число"""
    if money is None:
        return 0.0
    return float(money.units) + float(money.nano) / 1_000_000_000


def _get_instrument_name(client, figi: str, ticker: str = "") -> str:
    """Пытается получить нормальное название инструмента"""
    try:
        # Сначала пробуем найти по figi
        instrument = client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
            id=figi
        ).instrument
        if instrument.name:
            return instrument.name
    except Exception:
        pass

    # Если не получилось — возвращаем тикер или figi
    return ticker or figi


def get_portfolio() -> PortfolioInfo:
    """
    Получает понятную информацию о портфеле.
    """
    with invest_client.get_client() as client:
        account_id = invest_client.get_account_id()

        # Получаем портфель
        portfolio = client.operations.get_portfolio(account_id=account_id)

        # Общая стоимость портфеля
        total_value = _money_to_float(portfolio.total_amount_portfolio)

        # Свободные деньги (считаем только рубли)
        free_cash = 0.0
        for pos in portfolio.positions:
            if pos.instrument_type == "currency":
                # Берём только рубли
                if getattr(pos, "ticker", "") == "RUB" or pos.figi == "RUB000UTSTOM":
                    free_cash += _money_to_float(pos.quantity)

        # Если по какой-то причине не нашли — берём из total_amount_currencies
        if free_cash == 0:
            free_cash = _money_to_float(getattr(portfolio, "total_amount_currencies", None))

        # Собираем позиции по бумагам
        positions = []
        for pos in portfolio.positions:
            # Пропускаем валюты
            if pos.instrument_type == "currency":
                continue

            quantity = int(_money_to_float(pos.quantity))
            if quantity == 0:
                continue

            avg_price = _money_to_float(pos.average_position_price)
            cur_price = _money_to_float(pos.current_price)
            ticker = getattr(pos, "ticker", "") or ""
            figi = pos.figi

            # Получаем нормальное название
            name = _get_instrument_name(client, figi, ticker)

            positions.append(Position(
                figi=figi,
                ticker=ticker,
                name=name,
                quantity=quantity,
                average_price=avg_price,
                current_price=cur_price,
                value=quantity * cur_price
            ))

        return PortfolioInfo(
            total_value=total_value,
            free_cash=free_cash,
            positions=positions
        )