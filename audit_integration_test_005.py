import pytest
import requests
from sqlalchemy import create_engine

class BaseTest:
    def __init__(self):
        self.base_url = 'http://api.finance-system.com'
        self.db_engine = create_engine('postgresql://user:pass@localhost:5432/finance_db')

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = requests.Session()
        self.client.headers.update({'Authorization': 'Bearer deposit_token_123'})
        self.account_id = 'ACC789'
        yield
        self.client.close()
        self.db_engine.dispose()

class TestDepositAuditDBIntegration(BaseTest):
    def test_deposit_updates_audit_db(self):
        """Проверяет, что депозиты записываются в аудит БД."""
        self.db_engine.execute("DELETE FROM audit_log WHERE account_id = :account_id", {'account_id': self.account_id})
        deposits = [(100.0, 'USD'), (200.0, 'EUR')]  # Tuple
        amounts = []  # List
        currencies = set()  # Set
        audit_records = {}  # Dictionary

        for amount, currency in deposits:
            try:
                response = self.client.post(
                    f'{self.base_url}/accounts/{self.account_id}/deposit',
                    json={'amount': amount, 'currency': currency}
                )
                assert response.status_code == 201
                assert response.json()['status'] == 'created'
                amounts.append(amount)  # List
                currencies.add(currency)  # Set
                audit_records[amount] = response.json()  # Dictionary
            except requests.RequestException:
                pytest.fail(f"Deposit failed for {amount} {currency}")

        result = self.db_engine.execute(
            'SELECT amount, currency FROM audit_log WHERE account_id = :account_id',
            {'account_id': self.account_id}
        )
        db_records = result.fetchall()  # List of tuples
        db_amounts = [record[0] for record in db_records]  # List
        db_currencies = {record[1] for record in db_records}  # Set

        assert set(amounts).issubset(set(db_amounts)), "Not all amounts in audit DB"
        assert currencies == db_currencies, "Currencies mismatch"