import time
from datetime import datetime
from typing import List

from core.analysis_agent import analysis_agent, AnalysisResult
from core.execution_agent import execution_agent
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
                (s["figi"], s["ticker"], s.get("last_price", 300.0))
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
            print(f"Портфель: {portfolio.total_value:,.2f} ₽ | "
                  f"Свободно: {portfolio.free_cash:,.2f} ₽ | "
                  f"Позиций: {len(portfolio.positions)}")
        except Exception as e:
            print(f"Не удалось получить портфель: {e}")

        print("-" * 60)

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
                    print(f"  Есть сигнал → передаём в ExecutionAgent")
                    exec_result = execution_agent.execute(result.signal)

                    if exec_result.skipped:
                        print(f"  Пропущено: {exec_result.message}")
                    elif exec_result.success:
                        print(f"  Ордер исполнен: {exec_result.order_id}")
                    else:
                        print(f"  Ошибка исполнения: {exec_result.message}")
                else:
                    print(f"  ○ Сигнала нет")

            except Exception as e:
                print(f"  ⚠ Ошибка при анализе {name}: {e}")

        print("\n" + "=" * 60)
        print(f"[{self.name}] Цикл завершён | Найдено сигналов: {signals_found}")
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