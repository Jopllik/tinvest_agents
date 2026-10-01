from core.portfolio import get_portfolio

portfolio = get_portfolio()

print(f"Общая стоимость: {portfolio.total_value:,.2f} ₽")
print(f"Свободные деньги: {portfolio.free_cash:,.2f} ₽")
print(f"Количество позиций: {len(portfolio.positions)}\n")

if portfolio.positions:
    print("Открытые позиции:")
    for i, pos in enumerate(portfolio.positions, 1):
        print(f"{i}. {pos.ticker or pos.figi}")
        print(f"   Название:     {pos.name}")
        print(f"   Количество:   {pos.quantity} лот.")
        print(f"   Средняя цена: {pos.average_price:.2f} ₽")
        print(f"   Текущая цена: {pos.current_price:.2f} ₽")
        print(f"   Стоимость:    {pos.value:,.2f} ₽")
        print("-" * 45)
else:
    print("Открытых позиций нет.")