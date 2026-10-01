from core.execution_agent import execution_agent, TradeSignal

print("=== Тест ExecutionAgent ===\n")

# Сигнал на продажу оставшегося лота SBER
signal = TradeSignal(
    action="sell",
    figi="BBG004730N88",
    quantity=1,
    order_value_rub=270.0,
    reason="Тестовое закрытие позиции"
)

result = execution_agent.execute(signal)

print("\nРезультат исполнения:")
print(f"Успех: {result.success}")
print(f"Сообщение: {result.message}")
print(f"Order ID: {result.order_id}")
print(f"Signal ID: {result.signal_id}")
print(f"Торговый статус: {result.trading_status}")

if result.portfolio_after:
    print("\nПортфель после сделки:")
    print(f"  Общая стоимость: {result.portfolio_after.get('total_value', 0):,.2f} ₽")
    print(f"  Свободные деньги: {result.portfolio_after.get('free_cash', 0):,.2f} ₽")
    print(f"  Открытых позиций: {result.portfolio_after.get('positions_count', 0)}")