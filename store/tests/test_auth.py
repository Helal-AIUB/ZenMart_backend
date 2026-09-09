import pytest
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestAuthenticationAPI:
    @pytest.fixture
    def setup_user(self, api_client):
        user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!'
        }
        user = User.objects.create_user(**user_data)
        return {
            'user': user,
            'user_data': user_data,
            'client': api_client
        }

    def test_user_registration_success(self, api_client):
        payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewStrongPassword123!'
        }
        
        response = api_client.post('/auth/users/', payload)
        
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
        assert User.objects.filter(username='newuser').exists()

    def test_user_registration_duplicate_username_returns_400(self, setup_user):
        client = setup_user['client']
        
        payload = {
            'username': setup_user['user_data']['username'], 
            'email': 'another@example.com',
            'password': 'NewStrongPassword123!'
        }
        
        response = client.post('/auth/users/', payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_returns_jwt_tokens(self, setup_user):
        client = setup_user['client']
        
        payload = {
            'username': setup_user['user_data']['username'],
            'password': setup_user['user_data']['password']
        }
        
        response = client.post('/auth/jwt/create/', payload)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_with_invalid_credentials_returns_401(self, setup_user):
        client = setup_user['client']
        
        payload = {
            'username': setup_user['user_data']['username'],
            'password': 'wrongpassword'
        }
        
        response = client.post('/auth/jwt/create/', payload)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_without_token_returns_401(self, setup_user):
        client = setup_user['client']
        
        response = client.get('/auth/users/me/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_valid_token_returns_200(self, setup_user):
        client = setup_user['client']
        user = setup_user['user']
        
        client.force_authenticate(user=user)
        response = client.get('/auth/users/me/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username