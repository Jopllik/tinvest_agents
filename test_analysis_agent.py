from core.analysis_agent import analysis_agent
from core.execution_agent import execution_agent

FIGI = "BBG004730N88"  # SBER

print("=== Тест AnalysisAgent ===\n")

result = analysis_agent.analyze(
    figi=FIGI,
    quantity=1,
    order_value_rub=270.0
)

print(f"Свечей получено: {result.candles_count}")
print(f"Текущая цена: {result.current_price:.2f}")
print(f"SMA быстрая (5): {result.sma_fast:.2f}")
print(f"SMA медленная (15): {result.sma_slow:.2f}")
print(f"Причина: {result.reason}")

if result.signal:
    print(f"\nСгенерирован сигнал: {result.signal.action.upper()}")
    print("Передаём сигнал в ExecutionAgent...\n")
    
    exec_result = execution_agent.execute(result.signal)
    
    print(f"Результат исполнения: {exec_result.success}")
    print(f"Сообщение: {exec_result.message}")
    if exec_result.order_id:
        print(f"Order ID: {exec_result.order_id}")
else:
    print("\nСигнал не сгенерирован — ничего не делаем.")