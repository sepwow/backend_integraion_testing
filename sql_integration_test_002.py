import pytest
import requests
from sqlalchemy import create_engine

class BaseTest:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = requests.Session()
        self.client.headers.update({'Authorization': 'Bearer payment_token_789'})
        self.db_engine = create_engine('postgresql://user:pass@localhost:5432/finance_db')
        self.user_id = "USER789"
        self.base_url = "http://api.finance-system.com"
        yield
        self.client.close()
        self.db_engine.dispose()


class TestPaymentDBIntegration(BaseTest):
    def test_create_payment_updates_db(self):
        payment_response = self.client.post(f"{self.base_url}/payment",
                                            json={'user_id': self.user_id, 'amount': 75.0, 'currency': 'USD'})
        assert payment_response.status_code == 201
        result = self.db_engine.execute(f"SELECT amount, currency FROM payments WHERE user_id = :user_id",
                                        {'user_id': self.user_id})
        payment = result.fetchone()
        assert payment[0] == 75.0
        assert payment [1] == 'USD'