from core.instruments import get_filtered_shares, save_shares

print("Получаю и фильтрую акции...")
shares = get_filtered_shares(min_price=5.0, max_price=1000.0)

print(f"\nИтоговое количество: {len(shares)}")
print("\nПримеры (самые дешёвые):")
for s in shares[:10]:
    print(f"  {s.ticker:8} | {s.last_price:8.2f} ₽ | {s.name[:40]}")

print("\nПримеры (самые дорогие из отобранных):")
for s in shares[-5:]:
    print(f"  {s.ticker:8} | {s.last_price:8.2f} ₽ | {s.name[:40]}")

save_shares(shares)