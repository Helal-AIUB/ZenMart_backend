import pytest
from rest_framework import status
from django.contrib.auth.models import User
from store.models import Product, Collection
from model_bakery import baker

@pytest.mark.django_db
class TestProductAPI:
    
    def test_get_products_list_returns_200_and_valid_data(self, api_client):
        """Ensure public users can retrieve the product list."""
        collection = baker.make(Collection)
        baker.make(Product, collection=collection, _quantity=3)
        
        response = api_client.get('/store/products/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_product_by_normal_user_returns_403(self, api_client):
        """Ensure non-admin users cannot create a product."""
        # Authenticate as a normal user (non-staff)
        api_client.force_authenticate(user=User(is_staff=False))
        
        response = api_client.post('/store/products/', {'title': 'New Pet Food'})
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_product_by_admin_returns_201(self, api_client):
        """Ensure admin users can successfully create a product."""
        # Authenticate as an admin (staff)
        api_client.force_authenticate(user=User(is_staff=True))
        
        collection = baker.make(Collection)
        payload = {
            'title': 'Premium Dog Food',
            'slug': 'premium-dog-food',
            'unit_price': 150.00,
            'inventory': 50,
            'collection': collection.id
        }
        
        response = api_client.post('/store/products/', payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['id'] > 0
        assert response.data['title'] == 'Premium Dog Food'

    def test_delete_product_by_normal_user_returns_403(self, api_client):
        """Ensure non-admin users cannot delete a product."""
        # Authenticate as a normal user (non-staff)
        api_client.force_authenticate(user=User(is_staff=False))
        
        product = baker.make(Product)
        response = api_client.delete(f'/store/products/{product.id}/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN