from agents.base_agent import BaseAgent
from core.portfolio import get_portfolio
from tools.news_tools import get_news_for_tickers


class ResearchNewsAgent(BaseAgent):
    def run(self, tickers=None):
        print(f"\n=== {self.name} запущен ===\n")
        portfolio = self.get_portfolio()
        tickers = tickers or [pos.ticker for pos in portfolio.positions] if hasattr(portfolio, 'positions') else ["SBER"]
        news_data = get_news_for_tickers(tickers)
        print("Новостной фон по портфелю (RSS Interfax/ТАСС):")
        for item in news_data['news'][:3]:
            print(f"  {item['title']} | sentiment: {item.get('sentiment', 'neutral')}")
        print(f"Summary: {news_data['summary']}")
        print("Рекомендация: следовать SMA если новости neutral/positive. Negative — skip buys.")
        print("\n=== Агент завершил работу ===")
