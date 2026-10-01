from core.order_manager import place_market_order
from core.portfolio import get_portfolio

SBER_FIGI = "BBG004730N88"   # FIGI Сбера
LOT_PRICE_APPROX = 270.0     # примерная цена лота для риск-менеджера

def print_portfolio():
    portfolio = get_portfolio()
    print(f"Общая стоимость: {portfolio.total_value:,.2f} ₽")
    print(f"Свободные деньги: {portfolio.free_cash:,.2f} ₽")
    print(f"Открытых позиций: {len(portfolio.positions)}")
    for pos in portfolio.positions:
        print(f"  → {pos.name or pos.figi} | {pos.quantity} шт. | "
              f"ср.цена {pos.average_price:.2f} | тек.цена {pos.current_price:.2f}")
    print("-" * 50)


print("=== ТЕСТ ПОЛНОГО ЦИКЛА BUY → SELL ===\n")

# ---------- 1. Показываем текущий портфель ----------
print("1. Текущее состояние портфеля:")
print_portfolio()

# ---------- 2. Продаём 1 лот SBER ----------
print("2. Продаём 1 лот SBER...")
result = place_market_order(
    figi=SBER_FIGI,
    quantity=1,
    direction="sell",
    order_value_rub=LOT_PRICE_APPROX
)

if result.success:
    print(f"✅ Ордер на продажу успешно выставлен!")
    print(f"ID ордера: {result.order_id}")
    if hasattr(result, "trading_status") and result.trading_status:
        print(f"Торговый статус: {result.trading_status}")
else:
    print(f"❌ Ошибка при продаже: {result.message}")

print()

# ---------- 3. Смотрим портфель после продажи ----------
print("3. Состояние портфеля после продажи:")
print_portfolio()