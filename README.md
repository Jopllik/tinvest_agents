# tinvest_agents

Мультиагентная система трейдинга для Тинькофф Инвестиций.

## Правила (rules.txt)
- Капитал: 5000₽
- Max 7 позиций, покупки только при ≤4 позициях
- Только LONG, max 1000₽/лот
- Корзины: CHE/AVE/EXP по цене лота
- Sell at -1%, human confirms buys
- Только лонг позиции

## Структура
- core/: risk_manager, orchestrator, execution_agent, portfolio, order_manager
- agents/: market_data, monitoring, research_news, supervisor, etc.
- tests/: unit tests

## Обновления
- Устранены DeprecatedWarning для get_trading_status, share_by, post_order
- Обновлены вызовы на современные: get_instrument_by(InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI), instrument_id= вместо figi=
- Доработаны agents/monitoring.py и agents/research_news.py
- SDK: t_tech.invest

## Запуск dry-run
```bash
python test_orchestrator.py
# или
python -m test_orchestrator
```
auto_execute=False по умолчанию — только анализ, без реальных ордеров.

## Тесты
python -m pytest tests/ -q

Система следует rules.txt строго. Risk first.
