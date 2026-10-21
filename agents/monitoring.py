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
            chat_id = 'N/A'
            if call.message and hasattr(call.message, 'chat'):
                chat_id = call.message.chat.id
            print(f"[{self.name}] DEBUG: callback triggered data={call.data} chat={chat_id}")
            if self.chat_id and str(chat_id) != str(self.chat_id):
                self.bot.answer_callback_query(call.id)
                print(f"[{self.name}] DEBUG: chat id mismatch")
                return
            self.bot.answer_callback_query(call.id, "✅ Подтверждено" if call.data == "buy" else "❌ Отклонено")
            if call.data == "buy":
                self._process_buy_approval()
                self._send_decision_result("buy")
            elif call.data == "no":
                self.pending_proposals = []
                self._send_decision_result("no")
            print(f"[{self.name}] DEBUG: callback handled")
        @self.bot.message_handler(content_types=['text'])
        def handle_message(message):
            text = message.text.lower() if message.text else ''
            chat_id = 'N/A'
            if hasattr(message, 'chat') and hasattr(message.chat, 'id'):
                chat_id = message.chat.id
            print(f"[{self.name}] DEBUG: message received text='{message.text}' chat={chat_id}")
            if self.chat_id and str(chat_id) != str(self.chat_id):
                print(f"[{self.name}] DEBUG: chat id mismatch in message")
                return
            if any(k in text for k in ['buy', '✅', 'да', 'yes']):
                self._process_buy_approval()
                self._send_decision_result("buy")
            elif any(k in text for k in ['no', 'нет', '❌']):
                self.pending_proposals = []
                self._send_decision_result("no")
            print(f"[{self.name}] DEBUG: text message handled")
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
                    except Exception as e:
                        print(f"[{self.name}] TG exec msg error: {e}")
                    print(msg)
        self.pending_proposals = []

    def _send_decision_result(self, decision: str):
        print(f"[{self.name}] DEBUG: _send_decision_result called with {decision}, ensuring report sent")
        try:
            portfolio = self.get_portfolio()
        except Exception as e:
            print(f"[{self.name}] Portfolio API error in report: {e}. Using fallback.")
            portfolio = type('obj', (object,), {'total_value': 0, 'free_cash': 0, 'positions': []})()
        pos_count = len(getattr(portfolio, 'positions', []))
        bal = f"{getattr(portfolio, 'free_cash', 0):,.0f}"
        if not self.bot or not self.chat_id:
            print(f"\n=== Портфель после {decision.upper()} ===")
            print(f"Общая стоимость: {getattr(portfolio, 'total_value', 0):,.2f} ₽")
            print(f"Свободные деньги: {getattr(portfolio, 'free_cash', 0):,.2f} ₽")
            print(f"Позиций: {pos_count} / {risk_manager.max_open_positions}")
            if pos_count == 0: print("Открытых позиций нет.")
            return
        if decision == "buy":
            result_msg = f"✅ ордера выставлены, баланс {bal}₽, позиции {pos_count}. Следующий цикл автоматически."
            print(f"[{self.name}] DEBUG: buy report sent with bal={bal} pos={pos_count}")
        else:
            result_msg = f"❌ покупки отклонены, состояние портфеля: баланс {bal}₽, позиций {pos_count}, следующий цикл через 1ч."
            print(f"[{self.name}] DEBUG: no report sent with bal={bal} pos={pos_count}")
        try:
            self.bot.send_message(self.chat_id, result_msg)
            print(f"[{self.name}] Report message sent to TG with portfolio")
        except Exception as e:
            print(f"[{self.name}] TG send error: {e}")
        try:
            print(f"\n=== Портфель после {decision.upper()} ===")
            print(f"Общая стоимость: {getattr(portfolio, 'total_value', 0):,.2f} ₽")
            print(f"Свободные деньги: {getattr(portfolio, 'free_cash', 0):,.2f} ₽")
            print(f"Позиций: {pos_count} / {risk_manager.max_open_positions}")
            if pos_count == 0:
                print("Открытых позиций нет.")
        except Exception as e:
            print(f"[{self.name}] Console report print error: {e}")


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
        markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard=True)
        markup.add(
            types.KeyboardButton("✅ BUY"),
            types.KeyboardButton("❌ NO")
        )
        try:
            self.bot.send_message(int(self.chat_id), text, reply_markup=markup)
            print(f"[{self.name}] Предложения отправлены в Telegram с ReplyKeyboard. Ожидаем подтверждения.")
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


monitoring_agent = MonitoringAgent()
print(f"[{monitoring_agent.name}] Global instance created with TG bot.")
