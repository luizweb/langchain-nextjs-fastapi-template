from http import HTTPStatus

from app.schemas import ProjectPublic


def test_create_project(client, token):
    response = client.post(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Projeto de Teste',
            'description': 'Descrição do projeto',
            'llm_prompt': 'Prompt para LLM',
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'user_id': 1,
        'title': 'Projeto de Teste',
        'description': 'Descrição do projeto',
        'llm_prompt': 'Prompt para LLM',
    }


def test_create_project_with_minimal_data(client, token):
    response = client.post(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Projeto Simples',
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'user_id': 1,
        'title': 'Projeto Simples',
        'description': '',
        'llm_prompt': '',
    }


def test_read_projects_empty(client, token):
    response = client.get(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'projects': []}


def test_read_projects_with_projects(client, token, project):
    project_schema = ProjectPublic.model_validate(project).model_dump()
    response = client.get(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.json() == {'projects': [project_schema]}


def test_update_project(client, token, project):
    response = client.put(
        f'/projects/{project.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Projeto Atualizado',
            'description': 'Nova descrição',
            'llm_prompt': 'Novo prompt',
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'id': project.id,
        'user_id': project.user_id,
        'title': 'Projeto Atualizado',
        'description': 'Nova descrição',
        'llm_prompt': 'Novo prompt',
    }


def test_update_project_not_found(client, token):
    response = client.put(
        '/projects/999',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Projeto Inexistente',
            'description': 'Deve dar erro',
            'llm_prompt': 'Erro esperado',
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Project not found'}


def test_update_project_from_other_user(client, token, other_project):
    """Test updating project from another user raises not found"""
    response = client.put(
        f'/projects/{other_project.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Projeto de Outro Usuário',
            'description': 'Deve dar erro',
            'llm_prompt': 'Não autorizado',
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Project not found'}


def test_delete_project(client, token, project):
    response = client.delete(
        f'/projects/{project.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Project deleted'}


def test_delete_project_not_found(client, token):
    response = client.delete(
        '/projects/999',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Project not found'}


def test_delete_project_from_other_user(client, token, other_project):
    """Test deleting project from another user raises not found"""
    response = client.delete(
        f'/projects/{other_project.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Project not found'}


def test_create_project_unauthorized(client):
    """Test creating project without authentication raises 401"""
    response = client.post(
        '/projects/',
        json={
            'title': 'Projeto Sem Auth',
            'description': 'Deve dar erro',
            'llm_prompt': 'Não autorizado',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


def test_read_projects_unauthorized(client):
    """Test reading projects without authentication raises 401"""
    response = client.get('/projects/')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


def test_update_project_unauthorized(client, project):
    """Test updating project without authentication raises 401"""
    response = client.put(
        f'/projects/{project.id}',
        json={
            'title': 'Projeto Sem Auth',
            'description': 'Deve dar erro',
            'llm_prompt': 'Não autorizado',
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


def test_delete_project_unauthorized(client, project):
    """Test deleting project without authentication raises 401"""
    response = client.delete(f'/projects/{project.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


def test_create_multiple_projects(client, token):
    """Test creating multiple projects for the same user"""
    # Number of projects expected to be created
    EXPECTED_PROJECT_COUNT = 2

    response1 = client.post(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Projeto 1',
            'description': 'Primeiro projeto',
            'llm_prompt': 'Prompt 1',
        },
    )
    assert response1.status_code == HTTPStatus.CREATED

    response2 = client.post(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Projeto 2',
            'description': 'Segundo projeto',
            'llm_prompt': 'Prompt 2',
        },
    )
    assert response2.status_code == HTTPStatus.CREATED

    response_list = client.get(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response_list.status_code == HTTPStatus.OK
    projects = response_list.json()['projects']
    assert len(projects) == EXPECTED_PROJECT_COUNT
    assert projects[0]['title'] == 'Projeto 1'
    assert projects[1]['title'] == 'Projeto 2'


def test_project_isolation_between_users(client, token, other_project):
    """Test that users can only see their own projects"""
    response = client.get(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'projects': []}

    # Criar um projeto para o usuário atual
    client.post(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Meu Projeto',
            'description': 'Projeto do usuário atual',
            'llm_prompt': 'Prompt do usuário atual',
        },
    )

    response = client.get(
        '/projects/',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    projects = response.json()['projects']
    assert len(projects) == 1
    assert projects[0]['title'] == 'Meu Projeto'
    assert projects[0]['user_id'] == 1  # ID do usuário atual
