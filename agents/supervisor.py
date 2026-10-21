from core.orchestrator import orchestrator
from core.risk_manager import risk_manager
from core.risk_models import risk_models
from agents.base_agent import BaseAgent
from agents.research_news import ResearchNewsAgent
from agents.monitoring import monitoring_agent
from core.execution_agent import TradeSignal
from agents.monitoring import MonitoringAgent


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
        """Human-approval для покупок (rules.txt) via Telegram Monitoring."""
        if not proposals:
            return False
        monitoring = MonitoringAgent()
        sent = monitoring.send_buy_proposals(proposals)
        self.state["human_approved"] = sent  # async via bot callback
        return sent

    def run_full_cycle(self):
        """Полный цикл: news research -> update state -> risk check -> orchestrator -> final decision + TG if proposals."""
        news_agent = ResearchNewsAgent("ResearchNews")
        news_agent.run()
        self.update_state()
        print(f"[{self.name}] Цикл {self.state['cycle_count'] + 1}. Позиций: {self.state['positions_count']}")

        if not risk_models.can_buy_scan(self.state["positions_count"]):
            print(f"[{self.name}] Покупки заблокированы (позиций >4)")
            self.orchestrator.run_once()  # only stops
            self.state["cycle_count"] += 1
            return

        proposals = self.orchestrator.run_once()
        if proposals:
            print(f"[{self.name}] Получено {len(proposals)} proposals — вызов MonitoringAgent для TG подтверждения")
            monitoring_agent.send_buy_proposals(proposals)
            self.get_approval(proposals)
        else:
            # Mock for TG test (remove after)
            mock_proposals = [
                (TradeSignal("buy", "BBG000RMWQD4", 1, 500, "mock"), "EN+ (Эн+)", 500, 0.5),
                (TradeSignal("buy", "BBG004TC84Z8", 1, 600, "mock"), "Московский Кредитный Банк", 600, 0.3),
                (TradeSignal("buy", "BBG004S68B31", 1, 700, "mock"), "АЛРОСА", 700, 0.2)
            ]
            monitoring_agent.send_buy_proposals(mock_proposals)
            print(f"[{self.name}] Mock proposals sent to TG bot for test.")
        self.state["last_decision"] = "cycle_completed"
        self.state["cycle_count"] += 1
        print(f"[{self.name}] Цикл завершён. State: {self.state}")


supervisor = Supervisor()
print(f"[{supervisor.name}] Инициализирован с LangGraph-style state.")
