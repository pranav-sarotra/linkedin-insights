import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Page, Post, User


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CACHE_TYPE = 'simple'


@pytest.fixture
def app():
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_page(app):
    with app.app_context():
        page = Page(
            page_id='testcompany',
            linkedin_id='test123',
            name='Test Company',
            url='https://linkedin.com/company/testcompany',
            description='A test company for testing purposes',
            industry='Technology',
            follower_count=25000,
            employee_count=100,
            specialities='Testing,Development,QA'
        )
        db.session.add(page)
        db.session.flush()

        for i in range(5):
            post = Post(
                page_id=page.id,
                linkedin_post_id=f'post_{i}',
                content=f'Test post number {i}',
                like_count=100 + i * 10,
                comment_count=10 + i
            )
            db.session.add(post)

        for i in range(3):
            user = User(
                full_name=f'Test Employee {i}',
                headline='Software Engineer',
                company_id=page.id
            )
            db.session.add(user)

        db.session.commit()
        return page


def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_root_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'app' in data
    assert 'endpoints' in data


def test_get_all_pages_empty(client):
    response = client.get('/api/pages/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['data']['pages'] == []


def test_get_all_pages_with_data(client, sample_page):
    response = client.get('/api/pages/')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']['pages']) > 0
    assert data['data']['pages'][0]['name'] == 'Test Company'


def test_filter_by_followers(client, sample_page):
    response = client.get('/api/pages/?follower_range=20k-30k')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']['pages']) == 1

    response = client.get('/api/pages/?follower_range=50k-100k')
    data = response.get_json()
    assert len(data['data']['pages']) == 0


def test_search_by_name(client, sample_page):
    response = client.get('/api/pages/?name=Test')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']['pages']) == 1


def test_filter_by_industry(client, sample_page):
    response = client.get('/api/pages/?industry=Technology')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']['pages']) == 1


def test_pagination(client, sample_page):
    response = client.get('/api/pages/?page=1&per_page=5')
    assert response.status_code == 200
    data = response.get_json()
    assert 'pagination' in data['data']
    assert data['data']['pagination']['page'] == 1


def test_get_page_by_id(client, sample_page):
    response = client.get('/api/pages/testcompany')
    assert response.status_code == 200
    data = response.get_json()
    assert data['data']['name'] == 'Test Company'


def test_invalid_page_id(client):
    response = client.get('/api/pages/invalid@id!')
    assert response.status_code == 400


def test_get_page_posts(client, sample_page):
    response = client.get('/api/pages/testcompany/posts')
    assert response.status_code == 200
    data = response.get_json()
    assert 'posts' in data['data']
    assert len(data['data']['posts']) > 0


def test_get_page_employees(client, sample_page):
    response = client.get('/api/pages/testcompany/employees')
    assert response.status_code == 200
    data = response.get_json()
    assert 'employees' in data['data']


def test_page_not_found_posts(client):
    response = client.get('/api/pages/nonexistent/posts')
    assert response.status_code == 404


def test_page_not_found_employees(client):
    response = client.get('/api/pages/nonexistent/employees')
    assert response.status_code == 404