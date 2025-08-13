import pytest
import requests
from kafka import KafkaProducer, KafkaConsumer
from sqlalchemy import create_engine
import json

class BaseTest:
    def __init__(self): #Забыл почему здесь нужно __init__, а ниже просто setup?
        self.base_url = 'http://api.finance-system.com'
        self.db_engine = create_engine('postgresql://user:pass@localhost:5432/finance_db')

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = requests.Session()
        self.client.headers.update({'Authorization': 'Bearer notification_token_789'})
        self.user_id = 'USER123'
        yield
        self.client.close()
        self.db_engine.dispose() # new commit


class TestNotificationAuditDBIntegration(BaseTest):
    def test_notification_updates_audit_db(self):
        self.db_engine.execute(
            'DELETE FROM audit_log WHERE user_id = :user_id',
            {'user_id': self.user_id})
        notifications = [('Payment received', 'info'), ('Refund processed', 'warning')] # Откуда мы взяли этот кортеж? Что он значит?
        messages = [] # Почему здесь нужен именно список?
        types = set() # Почему здесь нужно именно множество?
        audit_records = {} # Мы знаем, что будем использовать ключ/значение и поэтому выбрали словарь?

        # Забыл что такое маппинг и что значит "message -> response JSON"
        for message, notification_type in notifications:
            try:
                response = self.client.post(
                    f'{self.base_url}/notifications',
                    json={'user_id': self.user_id, 'message': message, 'type': notification_type}
                )
                assert response.status_code == 201
                assert response.json()['status'] == 'sent'
                messages.append(message)
                types.add(notification_type)
                audit_records[message] = response.json()
            except requests.RequestException:
                pytest.fail(f"Deposit failed for {message} {notification_type}")

        result = self.db_engine.execute(
            'SELECT message, type FROM audit_log WHERE user_id = :user_id;',
            {'user_id': self.user_id}
        )
        db_records = result.fetchall()
        db_messages = [record[0] for record in db_records] # Здесь я тоже не помню что происходит
        db_types = {record[1] for record in db_records} # Здесь я тоже не помню что происходит

        assert set(messages).issubset(set(db_messages))
        assert types == db_types