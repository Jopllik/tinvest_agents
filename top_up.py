import os
from dotenv import load_dotenv
from t_tech.invest.sandbox.client import SandboxClient
from t_tech.invest import MoneyValue

load_dotenv()

TOKEN = os.getenv("INVEST_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")

if not TOKEN or not ACCOUNT_ID:
    print("Ошибка: проверь файл .env (нужны INVEST_TOKEN и ACCOUNT_ID)")
else:
    print("Пополняем счёт в песочнице на 100 000 ₽...")
    try:
        with SandboxClient(TOKEN) as client:
            # Пополняем на 100 000 рублей
            result = client.sandbox.sandbox_pay_in(
                account_id=ACCOUNT_ID,
                amount=MoneyValue(units=100000, nano=0, currency="rub")
            )
            print("Счёт успешно пополнен!")
            print(f"Текущий баланс: {result.balance.units} {result.balance.currency}")
    except Exception as e:
        print("Ошибка при пополнении:")
        print(e)
