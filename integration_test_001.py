import pytest
import requests

class BaseTest:
    @pytest.fixture(autouse=True)
    def setup_api_client(self):
        self.client = requests.Session()
        self.client.headers.update({'Authorization': 'Bearer initial_token_123'})
        self.user_id = "USER456"
        self.base_url = "https://api.finance-system.com"
        yield
        self.client.close()


class TestAuthAccountIntegration(BaseTest):
    def test_login_and_get_account(self):
        auth_response = self.client.post(f"{self.base_url}/auth/login",
                                         json={'user_id': self.user_id, 'password': 'secure_pass'})
        assert auth_response.status_code == 200
        token = auth_response.json()['token']
        self.client.headers.update({'Authorization': f'Bearer {token}'})

        account_response = self.client.get(f"{self.base_url}/accounts?user_id={self.user_id}")
        assert account_response.status_code == 200
        assert account_response.json()['account_id'] == 'ACC123'
        assert account_response.json()['balance'] == 1000.0