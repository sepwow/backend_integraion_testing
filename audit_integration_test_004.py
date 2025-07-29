import pytest
import requests
from sqlalchemy import create_engine
import time


class BaseTest:
    def __init__(self):
        self.base_url = 'http://api.finance-system.com'
        self.db_engine = create_engine('postgresql://user:pass@localhost:5432/finance_db')

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = requests.Session()
        self.client.headers.update({'Authorization': 'Bearer audit_token_789'})
        self.user_id = 'USER456'
        yield
        self.client.close()
        self.db_engine.dispose()


class TestTransactionAuditDBIntegration(BaseTest):
    @pytest.mark.parametrize('amount, currency', [(100.0, 'USD'), (200.0, 'EUR')])
    def test_transaction_updates_audit_db(self, amount, currency):
        """Проверяет, что транзакция записывается в аудит БД."""
        self.db_engine.execute("DELETE FROM audit_log WHERE user_id = :user_id", {'user_id': self.user_id})
        try:
            response = self.client.post(
                f'{self.base_url}/transactions',
                json={'user_id': self.user_id, 'amount': amount, 'currency': currency}
            )
            assert response.status_code == 201
        except requests.RequestException:
            pytest.fail("Transaction creation failed")

        attempts = 5
        audit = None
        while attempts > 0:
            try:
                with self.db_engine.connect() as connection:
                    result = connection.execute(
                        'SELECT amount, currency FROM audit_log WHERE user_id = :user_id',
                        {'user_id': self.user_id}
                    )
                    audit = result.fetchone()
                    if audit and audit['amount'] == amount and audit['currency'] == currency:
                        break
                    attempts -= 1
                    time.sleep(1)
            except Exception:
                pytest.fail('Database query failed')
        assert audit is not None, "Audit record not found"
        assert audit['amount'] == amount
        assert audit['currency'] == currency

    def test_transaction_logs_audit(self):
        """Проверяет, что транзакция логируется в сервисе аудита."""
        self.db_engine.execute("DELETE FROM audit_log WHERE user_id = :user_id", {'user_id': self.user_id})
        try:
            transactions_response = self.client.post(
                f'{self.base_url}/transactions',
                json={'user_id': self.user_id, 'amount': 150.0, 'currency': 'USD'}
            )
            assert transactions_response.status_code == 201
        except requests.RequestException:
            pytest.fail("Transaction creation failed")

        try:
            audit_response = self.client.get(f'{self.base_url}/audit?user_id={self.user_id}')
            assert audit_response.status_code == 200
            records = audit_response.json().get('records', [])
        except requests.RequestException:
            pytest.fail("Audit request failed")
        found = False
        for record in records:
            if record['amount'] != 150.0:
                continue
            found = True
            break
        assert found, "Audit record not found"