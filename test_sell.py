from core.order_manager import place_sell_order
from core.portfolio import get_portfolio

print("=== Тест продажи SBER ===\n")

FIGI = "BBG004730N88"   # SBER
QUANTITY = 1
ORDER_VALUE = 280       # примерно

result = place_sell_order(
    figi=FIGI,
    quantity=QUANTITY,
    order_value_rub=ORDER_VALUE
)

if result.success:
    print("✅ Ордер на продажу успешно выставлен!")
    print(f"ID ордера: {result.order_id}")
else:
    print("❌ Ордер отклонён")
    print(f"Причина: {result.message}")

print("\n--- Состояние портфеля после продажи ---")
portfolio = get_portfolio()
print(f"Общая стоимость: {portfolio.total_value:,.2f} ₽")
print(f"Свободные деньги: {portfolio.free_cash:,.2f} ₽")
print(f"Открытых позиций: {len(portfolio.positions)}")

# Покажем, остался ли SBER
sber_left = False
for pos in portfolio.positions:
    if pos.ticker == "SBER" or pos.figi == FIGI:
        sber_left = True
        print(f"\nSBER всё ещё есть: {pos.quantity} лот.")
        break

if not sber_left:
    print("\nSBER успешно закрыт.")