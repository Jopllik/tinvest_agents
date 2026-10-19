from core.instruments import get_filtered_shares, save_shares

print("Получаю и фильтрую акции по цене лота...")
shares = get_filtered_shares(max_lot_cost=1000.0)

print(f"\nИтоговое количество: {len(shares)}")
print("\nСамые дешёвые лоты:")
for s in shares[:10]:
    print(f"  {s.ticker:8} | акция {s.last_price:10.4f} | лот {s.lot:<6} | лот стоит {s.lot_cost:8.2f} ₽ | {s.name[:40]}")

print("\nСамые дорогие лоты из отобранных:")
for s in shares[-5:]:
    print(f"  {s.ticker:8} | акция {s.last_price:10.4f} | лот {s.lot:<6} | лот стоит {s.lot_cost:8.2f} ₽ | {s.name[:40]}")

save_shares(shares)