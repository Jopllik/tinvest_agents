from core.orchestrator import orchestrator

# Один раз прогнать анализ
orchestrator.run_once()

# Если хочешь запустить в цикле (каждые 15 минут) — раскомментируй:
# orchestrator.run_loop(interval_minutes=15)