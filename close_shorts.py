import time
from uuid import uuid4
from t_tech.invest import OrderDirection, OrderType, SecurityTradingStatus

from core.client import invest_client
from core.portfolio import get_portfolio


def quotation_ok(status) -> bool:
    return bool(status.market_order_available_flag and status.api_trade_available_flag)


print("=== Закрытие коротких позиций ===\n")

with invest_client.get_client() as client:
    account_id = invest_client.get_account_id()
    portfolio = get_portfolio()
    shorts = [p for p in portfolio.positions if p.quantity < 0]

    if not shorts:
        print("Коротких позиций нет.")
    else:
        for i, pos in enumerate(shorts):
            figi = pos.figi
            shares = abs(int(pos.quantity))

            status = client.market_data.get_trading_status(figi=figi)
            status_name = SecurityTradingStatus(status.trading_status).name

            if not quotation_ok(status):
                print(f"{pos.name or figi}: биржа закрыта ({status_name}) — пропуск")
                print("  Запусти скрипт после 10:00 МСК\n")
                continue

            share = client.instruments.share_by(
                id_type=1, class_code="", id=figi
            ).instrument
            lot = share.lot or 1
            lots = max(1, shares // lot)

            print(f"{pos.name or figi}: {pos.quantity} шт. | lot={lot} → BUY {lots} лот(ов)")

            try:
                response = client.orders.post_order(
                    figi=figi,
                    quantity=lots,
                    direction=OrderDirection.ORDER_DIRECTION_BUY,
                    account_id=account_id,
                    order_type=OrderType.ORDER_TYPE_MARKET,
                    order_id=str(uuid4()),
                )
                print(f"  OK  {response.order_id}")
            except Exception as e:
                print(f"  Ошибка: {e}")

            if i < len(shorts) - 1:
                time.sleep(1.2)  # не упираемся в лимит 2 req/s
            print()

print("=== Портфель ===")
p = get_portfolio()
print(f"Стоимость: {p.total_value:,.2f} ₽ | Свободно: {p.free_cash:,.2f} ₽ | Позиций: {len(p.positions)}")
for pos in p.positions:
    kind = "ШОРТ" if pos.quantity < 0 else "ЛОНГ"
    print(f"  [{kind}] {pos.name or pos.figi} | {pos.quantity} шт.")