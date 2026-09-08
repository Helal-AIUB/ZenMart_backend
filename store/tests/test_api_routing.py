import pytest
from rest_framework import status
from django.contrib.auth.models import User

@pytest.mark.django_db
class TestStoreAPIEndpoints:

    @pytest.mark.parametrize("endpoint", [
        '/store/products/',
        '/store/collections/',
        '/store/article-categories/',
        '/store/articles/',
    ])
    def test_public_endpoints_are_reachable(self, api_client, endpoint):
        """Ensure public GET endpoints are alive and return 200 OK."""
        response = api_client.get(endpoint)
        assert response.status_code == status.HTTP_200_OK

    def test_cart_creation_is_allowed(self, api_client):
        """Ensure anyone can create a new cart via POST."""
        response = api_client.post('/store/carts/')
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize("endpoint", [
        '/store/customers/',
        '/store/orders/',
        '/store/notifications/',
        '/store/coupons/',
    ])
    def test_protected_endpoints_reject_anonymous_users(self, api_client, endpoint):
        """Ensure sensitive endpoints reject unauthenticated requests."""
        response = api_client.get(endpoint)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @pytest.mark.parametrize("endpoint", [
        '/store/customers/',
        '/store/orders/',
        '/store/notifications/',
        '/store/coupons/',
    ])
    def test_protected_endpoints_allow_admin_access(self, api_client, endpoint):
        """Ensure admin users can access protected endpoints."""
        api_client.force_authenticate(user=User(is_staff=True))
        response = api_client.get(endpoint)
        assert response.status_code == status.HTTP_200_OK