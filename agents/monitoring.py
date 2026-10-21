from agents.base_agent import BaseAgent
from core.portfolio import get_portfolio
from core.risk_manager import risk_manager

class MonitoringAgent(BaseAgent):
    def run(self):
        print(f"\n=== {self.name} запущен ===\n")
        portfolio = self.get_portfolio()
        print(f"Общая стоимость: {portfolio.total_value:,.2f} ₽")
        print(f"Свободные деньги: {portfolio.free_cash:,.2f} ₽")
        print(f"Позиций: {len(portfolio.positions)} / {risk_manager.max_open_positions}")
        if not portfolio.positions:
            print("Открытых позиций нет.")
        else:
            print("Позиции:")
            for pos in portfolio.positions:
                side = "ЛОНГ" if pos.quantity > 0 else "ШОРТ"
                print(f"  {pos.ticker:6} {pos.name or '':20} {pos.quantity:6} {side} {pos.value:10,.2f} ₽")
        print("\n=== Агент завершил работу ===")
