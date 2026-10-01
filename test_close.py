from core.order_manager import close_position
from core.portfolio import get_portfolio

print("=== Закрытие позиции SBER ===\n")

result = close_position("SBER")

if result.success:
    print("✅ Позиция закрыта")
    print(f"ID ордера: {result.order_id}")
else:
    print("❌ Не удалось закрыть")
    print(f"Причина: {result.message}")

print("\n--- Портфель ---")
portfolio = get_portfolio()
print(f"Позиций: {len(portfolio.positions)}")
for pos in portfolio.positions:
    print(f"  {pos.ticker:6}  {pos.name:20}  {pos.quantity:6} лот.")