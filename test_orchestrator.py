from core.orchestrator import orchestrator
from agents.supervisor import supervisor

# Один раз прогнать анализ
orchestrator.run_once()

# Supervisor test (human-confirm будет запрошен при proposals)
print("\n=== Supervisor test ===")
supervisor.run_full_cycle()

# Если хочешь запустить в цикле (каждые 15 минут) — раскомментируй:
# orchestrator.run_loop(interval_minutes=15)
# supervisor.run_full_cycle() in loop