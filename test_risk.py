from core.risk_manager import risk_manager

print("=== Тест Risk Manager ===\n")

# 1. Текущая стоимость портфеля
portfolio_value = risk_manager.get_portfolio_value()
print(f"Стоимость портфеля: {portfolio_value:,.2f} ₽")

# 2. Количество открытых позиций
open_positions = risk_manager.get_open_positions_count()
print(f"Открытых позиций: {open_positions}")

print("\n--- Проверки ордеров ---\n")

# 3. Нормальный ордер (должен пройти)
test_value_1 = 15_000  # 15 тысяч рублей
result1 = risk_manager.can_open_position(test_value_1)
print(f"Ордер на {test_value_1:,} ₽ → {'РАЗРЕШЁН' if result1.allowed else 'ЗАПРЕЩЁН'}")
print(f"   Причина: {result1.reason}\n")

# 4. Слишком большой ордер (должен быть запрещён)
test_value_2 = 80_000  # 80 тысяч (больше лимита 50к)
result2 = risk_manager.can_open_position(test_value_2)
print(f"Ордер на {test_value_2:,} ₽ → {'РАЗРЕШЁН' if result2.allowed else 'ЗАПРЕЩЁН'}")
print(f"   Причина: {result2.reason}\n")

# 5. Ордер, который превышает % от портфеля
test_value_3 = portfolio_value * 0.25  # 25% от портфеля (лимит 10%)
result3 = risk_manager.can_open_position(test_value_3)
print(f"Ордер на {test_value_3:,.0f} ₽ (25% портфеля) → {'РАЗРЕШЁН' if result3.allowed else 'ЗАПРЕЩЁН'}")
print(f"   Причина: {result3.reason}")