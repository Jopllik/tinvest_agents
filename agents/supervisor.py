from core.orchestrator import orchestrator
from core.risk_manager import risk_manager
from core.risk_models import risk_models
from agents.base_agent import BaseAgent


class Supervisor(BaseAgent):
    """Supervisor / Orchestrator (координатор всех агентов, human-approval, final decision)."""
    def __init__(self):
        super().__init__("Supervisor")
        self.state = {
            "positions_count": 0,
            "last_decision": None,
            "human_approved": False,
            "cycle_count": 0,
        }
        self.orchestrator = orchestrator

    def update_state(self):
        """Обновляет состояние из портфеля и risk models."""
        try:
            portfolio = self.get_portfolio()
            self.state["positions_count"] = len(portfolio.positions) if hasattr(portfolio, 'positions') else risk_manager.get_open_positions_count()
            self.state["human_approved"] = False
        except Exception as e:
            print(f"[{self.name}] Ошибка обновления state: {e}")

    def get_approval(self, proposals: list) -> bool:
        """Human-approval для покупок (rules.txt)."""
        if not proposals:
            return False
        print(f"\n[{self.name}] Предложения на покупку ({len(proposals)}):")
        for p in proposals:
            print(f"  - {p}")
        print("Human, подтверждаете? (y/n)")
        approved = input().lower() == "y"
        self.state["human_approved"] = approved
        return approved

    def run_full_cycle(self):
        """Полный цикл: update state -> risk check -> orchestrator -> final decision."""
        self.update_state()
        print(f"[{self.name}] Цикл {self.state['cycle_count'] + 1}. Позиций: {self.state['positions_count']}")

        if not risk_models.can_buy_scan(self.state["positions_count"]):
            print(f"[{self.name}] Покупки заблокированы (позиций >4)")
            self.orchestrator.run_once()  # only stops
            self.state["cycle_count"] += 1
            return

        self.orchestrator.run_once()
        self.state["last_decision"] = "cycle_completed"
        self.state["cycle_count"] += 1
        print(f"[{self.name}] Цикл завершён. State: {self.state}")


supervisor = Supervisor()
print(f"[{supervisor.name}] Инициализирован с LangGraph-style state.")
