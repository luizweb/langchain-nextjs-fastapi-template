from http import HTTPStatus

from freezegun import freeze_time
from jwt import decode, encode

from app.security import create_access_token, settings


def test_jwt():
    data = {'test': 'test'}
    token = create_access_token(data)

    decoded = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )

    assert decoded['test'] == data['test']
    assert 'exp' in decoded


def test_jwt_invalid_token(client):
    response = client.delete(
        '/users/1', headers={'Authorization': 'Bearer token-invalido'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_jwt_token_without_sub(client):
    """Test token without 'sub' field raises credentials exception"""
    # Criar token sem o campo 'sub'
    token = encode(
        {'some_field': 'some_value'},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.delete(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_jwt_token_with_empty_sub(client):
    """Test token with empty 'sub' field raises credentials exception"""
    # Criar token com 'sub' vazio
    token = encode(
        {'sub': ''},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.delete(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_jwt_token_with_nonexistent_user(client):
    """Test token with valid 'sub' but user doesn't exist in database"""
    # Criar token com email que não existe no banco
    token = encode(
        {'sub': 'nonexistent@user.com'},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.delete(
        '/users/1',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_jwt_token_expired(client, user):
    """Test expired token raises credentials exception"""
    with freeze_time('2023-07-14 12:00:00'):
        token = create_access_token(data={'sub': user.email})

    # Avançar o tempo para depois da expiração (30 minutos)
    with freeze_time('2023-07-14 12:31:00'):
        response = client.delete(
            f'/users/{user.id}',
            headers={'Authorization': f'Bearer {token}'},
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Could not validate credentials'}
