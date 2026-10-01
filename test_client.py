from core.client import invest_client

print(invest_client)

with invest_client.get_client() as client:
    accounts = client.users.get_accounts()
    print("\nАккаунты:")
    for acc in accounts.accounts:
        print(f"  ID: {acc.id}")
        print(f"  Name: {acc.name}")
        print(f"  Status: {acc.status}")
        print("-" * 40)