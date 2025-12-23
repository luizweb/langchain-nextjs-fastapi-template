from http import HTTPStatus


def test_fastapi_health_check(client):
    response = client.get('/health_check')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'FastAPI is running!'}
