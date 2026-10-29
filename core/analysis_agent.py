from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timedelta
import time

from t_tech.invest import CandleInterval, HistoricCandle
from core.client import invest_client
from core.execution_agent import TradeSignal
from core.portfolio import get_portfolio


def quotation_to_decimal(q):
    """Простое преобразование Quotation → float"""
    return float(q.units) + float(q.nano) / 1_000_000_000


@dataclass
class AnalysisResult:
    signal: Optional[TradeSignal]
    reason: str
    current_price: float
    sma_fast: float
    sma_slow: float
    candles_count: int


class AnalysisAgent:
    """
    Аналитический агент.
    Смотрит историю свечей → считает индикаторы → генерирует TradeSignal.
    """

    def __init__(self):
        self.name = "AnalysisAgent"
        self.fast_period = 5      # быстрая SMA
        self.slow_period = 15     # медленная SMA

    def _get_candles(self, figi: str, days: int = 5) -> List[HistoricCandle]:
        """Получаем минутные свечи за последние N дней с retry на UNAVAILABLE"""
        for attempt in range(3):
            try:
                with invest_client.get_client() as client:
                    now = datetime.utcnow()
                    from_ = now - timedelta(days=days)

                    candles = client.market_data.get_candles(
                        figi=figi,
                        from_=from_,
                        to=now,
                        interval=CandleInterval.CANDLE_INTERVAL_15_MIN  # 15-минутные свечи
                    ).candles

                    return candles
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"[{self.name}] Candle fetch attempt {attempt+1} failed: {e}. Retrying in {5 * (attempt+1)}s...")
                time.sleep(5 * (attempt+1))
        return []

    def _calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period

    def analyze(self, figi: str, quantity: int = 1, order_value_rub: float = 300.0) -> AnalysisResult:
        """
        Главный метод аналитика.
        Возвращает AnalysisResult с возможным сигналом.
        """
        print(f"[{self.name}] Анализирую {figi}...")

        try:
            candles = self._get_candles(figi)
        except Exception as e:
            return AnalysisResult(
                signal=None,
                reason=f"Ошибка получения свечей: {e}",
                current_price=0.0,
                sma_fast=0.0,
                sma_slow=0.0,
                candles_count=0
            )

        if len(candles) < self.slow_period + 2:
            return AnalysisResult(
                signal=None,
                reason=f"Недостаточно свечей ({len(candles)}). Нужно минимум {self.slow_period + 2}",
                current_price=0.0,
                sma_fast=0.0,
                sma_slow=0.0,
                candles_count=len(candles)
            )

        # Берём цены закрытия
        closes = [float(quotation_to_decimal(c.close)) for c in candles]
        current_price = closes[-1]

        sma_fast = self._calculate_sma(closes, self.fast_period)
        sma_slow = self._calculate_sma(closes, self.slow_period)
        prev_sma_fast = self._calculate_sma(closes[:-1], self.fast_period)
        prev_sma_slow = self._calculate_sma(closes[:-1], self.slow_period)

        if None in (sma_fast, sma_slow, prev_sma_fast, prev_sma_slow):
                return AnalysisResult(
                signal=None,
                reason="Не удалось посчитать SMA",
                current_price=current_price,
                sma_fast=sma_fast or 0.0,
                sma_slow=sma_slow or 0.0,
                candles_count=len(candles)
            )

        signal = None
        reason = "Нет сигнала (нет пересечения)"

        min_gap_percent = 0.00005  # 0.005% to have 4-9 signals per rules, not too strict
        gap = abs(sma_fast - sma_slow)
        gap_percent = gap / sma_slow if sma_slow > 0 else 0
        crossed_up = prev_sma_fast <= prev_sma_slow and sma_fast > sma_slow
        crossed_down = prev_sma_fast >= prev_sma_slow and sma_fast < sma_slow

        if (crossed_up or crossed_down) and gap_percent < min_gap_percent:
            reason = f"Пересечение слишком слабое: разрыв {gap_percent:.4f}% < {min_gap_percent:.4f}%"
        elif crossed_up:
            signal = TradeSignal(
                action="buy",
                figi=figi,
                quantity=quantity,
                order_value_rub=order_value_rub,
                reason=f"Быстрая SMA({self.fast_period}) пересекла медленную SMA({self.slow_period}) снизу вверх"
            )
            reason = signal.reason
        elif crossed_down:
            # Only generate sell for owned LONG positions (per user request)
            portfolio = get_portfolio()
            if not any(p.figi == figi for p in getattr(portfolio, 'positions', [])):
                reason = f"No position for {figi} — no sell signal"
            else:
                signal = TradeSignal(
                    action="sell",
                    figi=figi,
                    quantity=quantity,
                    order_value_rub=order_value_rub,
                    reason=f"Быстрая SMA({self.fast_period}) пересекла медленную SMA({self.slow_period}) сверху вниз"
                )
                reason = signal.reason

        # Быстрая SMA пересекла медленную сверху вниз → SELL (only for owned)
        elif prev_sma_fast >= prev_sma_slow and sma_fast < sma_slow:
            portfolio = get_portfolio()
            if not any(p.figi == figi for p in getattr(portfolio, 'positions', [])):
                reason = f"No position for {figi} — no sell signal"
            else:
                signal = TradeSignal(
                    action="sell",
                    figi=figi,
                    quantity=quantity,
                    order_value_rub=order_value_rub,
                    reason=f"Быстрая SMA({self.fast_period}) пересекла медленную SMA({self.slow_period}) сверху вниз"
                )
                reason = signal.reason

        return AnalysisResult(
            signal=signal,
            reason=reason,
            current_price=current_price,
            sma_fast=sma_fast,
            sma_slow=sma_slow,
            candles_count=len(candles)
        )


# Глобальный экземпляр
analysis_agent = AnalysisAgent()