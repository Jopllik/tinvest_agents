from agents.base_agent import BaseAgent
from core.risk_manager import risk_manager


class RiskPortfolioAgent(BaseAgent):
    """Агент портфеля и рисков. Пока только показывает состояние."""

    def run(self):
        print(f"\n=== {self.name} запущен ===\n")

        portfolio = self.get_portfolio()

        print(f"Общая стоимость: {portfolio.total_value:,.2f} ₽")
        print(f"Свободные деньги: {portfolio.free_cash:,.2f} ₽")
        print(f"Позиций: {len(portfolio.positions)}")
        print(f"Лимит позиций: {risk_manager.max_open_positions}\n")

        if not portfolio.positions:
            print("Открытых позиций нет.")
            print("\n=== Агент завершил работу ===")
            return

        print("Позиции:")
        for pos in portfolio.positions:
            side = "ЛОНГ" if pos.quantity > 0 else "ШОРТ"
            print(
                f"  {pos.ticker:6}  {pos.name:20}  "
                f"{pos.quantity:6} лот.  {side:4}  "
                f"{pos.value:10,.2f} ₽"
            )

        print("\n=== Агент завершил работу ===")