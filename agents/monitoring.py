from agents.base_agent import BaseAgent
from core.portfolio import get_portfolio
from core.risk_manager import risk_manager
from core.config import settings
from core.execution_agent import execution_agent, TradeSignal
import telebot
from telebot import types
import threading
import time


class MonitoringAgent(BaseAgent):
    def __init__(self, name="MonitoringAgent"):
        super().__init__(name)
        self.bot = None
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.pending_proposals = []
        self._bot_thread = None
        if settings.TELEGRAM_BOT_TOKEN and self.chat_id:
            self.bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN)
            self._register_handlers()
            print(f"[{self.name}] Telegram bot initialized for chat {self.chat_id}")

    def _register_handlers(self):
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            if str(call.message.chat.id) != str(self.chat_id):
                return
            if call.data == "buy":
                self.bot.answer_callback_query(call.id, "✅ Подтверждено")
                self._process_buy_approval()
            elif call.data == "no":
                self.bot.answer_callback_query(call.id, "❌ Отклонено")
                self.bot.send_message(self.chat_id, "Покупки отклонены (rules.txt)")
                self.pending_proposals = []
        print(f"[{self.name}] Telegram handlers registered")

    def _process_buy_approval(self):
        if not self.pending_proposals:
            return
        print(f"[{self.name}] Buy confirmed via Telegram. Sending to execution_agent...")
        for p in self.pending_proposals[:3]:
            if isinstance(p, tuple) and len(p) > 0:
                signal = p[0]
                name = p[1] if len(p) > 1 else "Unknown"
                if isinstance(signal, TradeSignal):
                    result = execution_agent.execute(signal)
                    msg = f"✅ {name}: {result.message}"
                    try:
                        self.bot.send_message(self.chat_id, msg)
                    except:
                        pass
                    print(msg)
        self.pending_proposals = []

    def send_buy_proposals(self, proposals: list):
        """Отправляет 3 предложения из корзин (ticker, lot_cost, gap%) в Telegram с кнопками buy/no."""
        if not self.bot or not self.chat_id or not proposals:
            print(f"[{self.name}] Нет Telegram config или proposals. Fallback to console.")
            return False
        self.pending_proposals = proposals[:3]
        text = "📈 Предложения к покупке (3 из корзин CHE/AVE/EXP):\n\n"
        for i, p in enumerate(self.pending_proposals, 1):
            if isinstance(p, tuple) and len(p) >= 4:
                signal, name, lot_cost, gap_percent = p[0], p[1], p[2], p[3]
                text += f"{i}. {name}\n   Лот: {lot_cost:.0f}₽ | Gap: {gap_percent:.2f}%\n"
        text += "\nПодтвердить покупку всех 3?"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ BUY", callback_data="buy"),
            types.InlineKeyboardButton("❌ NO", callback_data="no")
        )
        try:
            self.bot.send_message(int(self.chat_id), text, reply_markup=markup)
            print(f"[{self.name}] Предложения отправлены в Telegram. Ожидаем подтверждения.")
            return True
        except Exception as e:
            print(f"[{self.name}] Ошибка отправки в TG: {e}")
            return False

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
        if self.bot and not self._bot_thread:
            def bot_polling():
                print(f"[{self.name}] Telegram polling запущен (daemon thread)")
                self.bot.polling(none_stop=True, interval=1)
            self._bot_thread = threading.Thread(target=bot_polling, daemon=True)
            self._bot_thread.start()
            time.sleep(2)
        print("\n=== Агент завершил работу ===")
