import pytest
import requests
from sqlalchemy import create_engine

class BaseTest:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = requests.Session()
        self.client.headers.update({'Authorization': 'Bearer transaction_token_456'})
        self.db_engine = create_engine('postgresql://user:pass@localhost:5432/finance_db')
        self.user_id = "USER123"
        self.base_url = 'http://api.finance-system.com'
        yield
        self.client.close()
        self.db_engine.dispose()


class TestTransactionNotificationDBIntegration(BaseTest):
    @pytest.mark.parametrized('amount, currency', [(100.0, 'USD'), (200.0, 'EUR')])
    def test_create_transaction_updates_db(self, amount, currency):
        body = {'user_id': self.user_id, 'amount': amount, 'currency': currency}
        response = self.client.post(f'{self.base_url}/transactions', json=body)
        if response.status_code != 201:
            pytest.fail(f"Transaction creation failed: {response.text}")
        assert response.status_code == 201

        result = self.db_engine.execute(
            'SELECT amount, currency FROM transactions WHERE user_id = :user_id',
            {'user_id': self.user_id}
        )
        transaction = result.fetchone()
        assert transaction is not None, "Transaction not found in database"
        assert transaction [0] == amount
        assert transaction[1] == currency

    def test_transaction_sends_notification(self):
        response = self.client.post(f'{self.base_url}/transactions',
                         json={'amount': 150.0, 'currency': 'USD'})
        if response.status_code != 201:
            pytest.fail(f"Transaction creation failed: {response.text}")
        assert response.status_code == 201
        assert response.json()['status'] == 'created'

        notification_response = self.client.get(f'{self.base_url}/notifications?user_id={self.user_id}')
        assert notification_response.status_code == 200
        assert notification_response.json()['message'] == 'Transaction created'