import os
from dotenv import load_dotenv
from t_tech.invest.sandbox.client import SandboxClient

load_dotenv()

TOKEN = os.getenv("INVEST_TOKEN")

if not TOKEN:
    print("Ошибка: токен не найден")
else:
    print("Подключаемся к песочнице и создаём счёт...")
    try:
        with SandboxClient(TOKEN) as client:
            # Создаём новый счёт в песочнице
            new_account = client.sandbox.open_sandbox_account(name="MyTestAccount")
            print("Счёт успешно создан!")
            print(f"ID счёта: {new_account.account_id}")

            # Проверяем список счетов
            accounts = client.users.get_accounts()
            print(f"\nВсего счетов сейчас: {len(accounts.accounts)}")
            for acc in accounts.accounts:
                print(f"- ID: {acc.id} | Название: {acc.name}")
    except Exception as e:
        print("Ошибка:")
        print(e)