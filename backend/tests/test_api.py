from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_health() -> None:
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'


def test_parent_history_returns_list() -> None:
    response = client.get('/api/v1/parent/history')
    assert response.status_code == 200
    assert isinstance(response.json(), list)
