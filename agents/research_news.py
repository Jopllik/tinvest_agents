from agents.base_agent import BaseAgent
from core.portfolio import get_portfolio

class ResearchNewsAgent(BaseAgent):
    def run(self, ticker="SBER"):
        print(f"\n=== {self.name} запущен ===\n")
        print(f"Исследование новостей и фундаментала для {ticker}")
        portfolio = self.get_portfolio()
        print("Проверка новостного фона по портфелю...")
        for pos in portfolio.positions:
            print(f"  Анализ {pos.ticker}: сигнал нейтральный (mock)")
        print("Новостной фон: без критических событий.")
        print("Рекомендация: следовать техническим сигналам SMA.")
        print("\n=== Агент завершил работу ===")
