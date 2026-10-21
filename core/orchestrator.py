import time
from datetime import datetime
from typing import List

from core.analysis_agent import analysis_agent, AnalysisResult
from core.execution_agent import execution_agent, TradeSignal
from core.portfolio import get_portfolio
from core.instruments import load_shares_from_file


class Orchestrator:
    """
    Главный оркестратор мультиагентной системы.
    Запускает аналитика → получает сигналы → передаёт их исполнителю.
    """

    def __init__(self):
        self.name = "Orchestrator"
        self.quantity = 1  # по сколько лотов торговать

        # Загружаем отфильтрованный список акций
        shares = load_shares_from_file("filtered_shares.json")

        if not shares:
            print("Файл filtered_shares.json не найден или пуст. Используется запасной список.")
            self.instruments = [
                ("BBG004730N88", "SBER", 270.0),
            ]
        else:
            self.instruments = [
                (s["figi"], f"{s['ticker']} {s.get('name', '')}".strip(), s.get("lot_cost", s.get("last_price", 300.0)))
                for s in shares
            ]
            print(f"Загружено {len(self.instruments)} акций из filtered_shares.json")

        print(f"Режим исполнения: auto_execute={execution_agent.auto_execute}")

    def run_once(self):
        """Один полный цикл анализа всех инструментов"""
        print("\n" + "=" * 60)
        print(f"[{self.name}] Запуск цикла | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Показываем текущий портфель
        try:
            portfolio = get_portfolio()
            positions_count = len(portfolio.positions)
            print(f"Портфель: {portfolio.total_value:,.2f} ₽ | "
                  f"Свободно: {portfolio.free_cash:,.2f} ₽ | "
                  f"Позиций: {positions_count}")
        except Exception as e:
            print(f"Не удалось получить портфель: {e}")
            print("Покупки не ищем: портфель не прочитан.")
            return
        for pos in portfolio.positions:
            if pos.quantity <= 0 or pos.average_price <= 0 or pos.current_price <= 0:
                continue
            drop = (pos.current_price - pos.average_price) / pos.average_price
            if drop > -0.01:
                continue
            print(
                f"Стоп −1%: {pos.ticker or pos.name} "
                f"покупка {pos.average_price:.2f} → сейчас {pos.current_price:.2f} "
                f"({drop:.2%})"
            )
            stop_signal = TradeSignal(
                action="sell",
                figi=pos.figi,
                ticker=pos.ticker,
                quantity=1,
                order_value_rub=pos.value,
                reason="Стоп: цена на 1% ниже цены покупки",
            )
            exec_result = execution_agent.execute(stop_signal)
            if exec_result.skipped:
                print(f"  Пропущено: {exec_result.message}")
            elif exec_result.success:
                print(f"  Ордер исполнен: {exec_result.order_id}")
            else:
                print(f"  Ошибка исполнения: {exec_result.message}")

        if positions_count > 4:
            print("Позиций больше 4 — новые покупки не ищем.")
            print("=" * 60)
            return

        print("-" * 60)
        buy_signals = []
        signals_found = 0
        for figi, name, approx_price in self.instruments:
            print(f"\n→ Анализируем {name} ({figi})")

            try:
                result: AnalysisResult = analysis_agent.analyze(
                    figi=figi,
                    quantity=self.quantity,
                    order_value_rub=approx_price
                )

                print(f"  Цена: {result.current_price:.2f} | "
                      f"SMA5: {result.sma_fast:.2f} | "
                      f"SMA15: {result.sma_slow:.2f}")
                print(f"  {result.reason}")

                if result.signal:
                    signals_found += 1
                    if result.signal.action == "buy":
                        if any(p.figi == figi for p in portfolio.positions):
                            print("  Уже в портфеле — skip")
                            continue
                        lot_cost = getattr(result.signal, 'order_value_rub', approx_price)
                        if lot_cost > portfolio.free_cash or lot_cost > 1000 or lot_cost < 0.01:
                            print(f"  Lot {lot_cost:.0f}₽ — недостаточно средств или вне лимита")
                            continue
                        gap_percent = 0.0
                        gap_rub = 0.0
                        if result.sma_slow and result.sma_slow > 0:
                            gap_percent = (result.sma_fast - result.sma_slow) / result.sma_slow * 100
                            gap_rub = result.sma_fast - result.sma_slow
                        buy_signals.append((result.signal, name, lot_cost, gap_percent, gap_rub, result))
                        print(f"  BUY сигнал собран (gap {gap_percent:.3f}%)")
                    else:  # sell
                        profit_ok = False
                        for pos in portfolio.positions:
                            if pos.figi == figi:
                                profit = (pos.current_price - pos.average_price) / pos.average_price
                                if profit >= 0.01:
                                    profit_ok = True
                                    print(f"  +{profit:.1%} profit — SMA-sell OK")
                                else:
                                    print(f"  SMA-sell blocked: profit {profit:.1%} < +1%")
                                break
                        if profit_ok:
                            print(f"  Есть сигнал SELL → передаём в ExecutionAgent")
                            exec_result = execution_agent.execute(result.signal)
                            if exec_result.skipped:
                                print(f"  Пропущено: {exec_result.message}")
                            elif exec_result.success:
                                print(f"  Ордер исполнен: {exec_result.order_id}")
                            else:
                                print(f"  Ошибка исполнения: {exec_result.message}")
                        else:
                            print("  ○ SMA-sell отклонен (нет +1%)")
                else:
                    print(f"  ○ Сигнала нет")

            except Exception as e:
                print(f"  ⚠ Ошибка при анализе {name}: {e}")

        # Basket logic per rules.txt: CHE(0-100), AVE(100-500), EXP(500-1000)
        if buy_signals:
            baskets = {"CHE": [], "AVE": [], "EXP": []}
            for sig_tuple in buy_signals:
                _, _, lot_cost, _, _, _ = sig_tuple
                if lot_cost < 100:
                    b = "CHE"
                elif lot_cost < 500:
                    b = "AVE"
                else:
                    b = "EXP"
                baskets[b].append(sig_tuple)
            print(f"\nКорзины: CHE={len(baskets.get('CHE',[]))}, AVE={len(baskets.get('AVE',[]))}, EXP={len(baskets.get('EXP',[]))}")

            selected = []
            for bname in ["CHE", "AVE", "EXP"]:
                bs = baskets.get(bname, [])
                if bs:
                    sorted_b = sorted(bs, key=lambda x: (-x[3], -x[4]))
                    strongest = sorted_b[0]
                    selected.append(strongest)
                    print(f"Strongest {bname}: {strongest[1]} gap={strongest[3]:.3f}%")

            if len(selected) < 3 and len(buy_signals) >= 3:
                used_figis = {s[0].figi for s in selected}
                remaining = [s for s in buy_signals if s[0].figi not in used_figis]
                if remaining:
                    sorted_rem = sorted(remaining, key=lambda x: (-x[3], -x[4]))
                    for s in sorted_rem:
                        if len(selected) < 3:
                            selected.append(s)
                            print(f"Дополняем strongest overall: {s[1]}")

            if len(selected) >= 3:
                print("\nПредлагаем max 3 бумаги (по корзинам/strongest):")
                for s in selected[:3]:
                    print(f"  {s[1]} ({s[2]:.0f}₽ gap={s[3]:.3f}%)")
                print("Подтвердите покупку этих 3 бумаг? (y/n)")
                if input().lower() == 'y':
                    print("Human confirmed — executing buys (if auto_execute=True)")
                    for s in selected[:3]:
                        exec_result = execution_agent.execute(s[0])
                        print(f"  {s[1]}: {exec_result.message}")
                else:
                    print("Human rejected — buys skipped per rules.txt")
            else:
                print(f"Годных <3 ({len(selected)}), предложение не отправляется.")

        print("\n" + "=" * 60)
        print(f"[{self.name}] Цикл завершён | Buy-сигналов: {len(buy_signals)}")
        print("=" * 60)

    def run_loop(self, interval_minutes: int = 15):
        """
        Запускает оркестратор в бесконечном цикле.
        Каждые interval_minutes минут делает новый анализ.
        """
        print(f"[{self.name}] Запущен в режиме цикла (интервал {interval_minutes} мин)")
        print("Для остановки нажми Ctrl+C\n")

        try:
            while True:
                self.run_once()
                print(f"\nЖдём {interval_minutes} минут до следующего цикла...")
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print(f"\n[{self.name}] Остановлен пользователем")


# Глобальный экземпляр
orchestrator = Orchestrator()