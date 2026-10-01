from core.execution_agent import execution_agent, TradeSignal
from core.portfolio import get_portfolio

print("=== 1. Текущий портфель ===")
p = get_portfolio()
print(f"Стоимость: {p.total_value:,.2f} ₽")
print(f"Свободно: {p.free_cash:,.2f} ₽")
print(f"Позиций: {len(p.positions)}")
for pos in p.positions:
    print(f"  {pos.name or pos.figi} | {pos.quantity} шт. | {pos.current_price:.2f} ₽")

print("\n=== 2. Режим агента ===")
print(f"auto_execute = {execution_agent.auto_execute}")
if execution_agent.auto_execute:
    print("ВНИМАНИЕ: ордера будут выставляться!")
else:
    print("ОК: ордера выставляться не должны")

print("\n=== 3. SELL бумаги, которой нет в портфеле ===")
result = execution_agent.execute(TradeSignal(
    action="sell",
    figi="BBG004730N88",  # SBER
    quantity=1,
    order_value_rub=270.0,
    ticker="SBER",
    reason="Тест: продажа без позиции"
))
print(f"success={result.success}  skipped={result.skipped}")
print(f"message={result.message}")