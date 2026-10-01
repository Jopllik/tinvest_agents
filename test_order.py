from core.order_manager import place_market_order
from core.portfolio import get_portfolio

print("=== Тест выставления ордера ===\n")

# Берём Сбербанк (очень ликвидная бумага)
FIGI = "BBG004730N88"      # SBER
QUANTITY = 1               # 1 лот
APPROX_PRICE = 270         # примерная цена одной акции
ORDER_VALUE = QUANTITY * APPROX_PRICE   # ≈ 270 рублей

print(f"Пытаемся купить {QUANTITY} лот SBER (~{ORDER_VALUE} ₽)")
print("Сначала проверка через риск-менеджер...\n")

result = place_market_order(
    figi=FIGI,
    quantity=QUANTITY,
    direction="buy",
    order_value_rub=ORDER_VALUE
)

if result.success:
    print("✅ Ордер успешно выставлен!")
    print(f"ID ордера: {result.order_id}")
else:
    print("❌ Ордер отклонён")
    print(f"Причина: {result.message}")

print("\n--- Текущее состояние портфеля ---")
portfolio = get_portfolio()
print(f"Общая стоимость: {portfolio.total_value:,.2f} ₽")
print(f"Свободные деньги: {portfolio.free_cash:,.2f} ₽")
print(f"Открытых позиций: {len(portfolio.positions)}")