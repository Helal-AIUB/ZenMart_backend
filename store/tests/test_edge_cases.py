import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from store.models import Product, Collection, Cart, CartItem

User = get_user_model()

@pytest.mark.django_db
class TestECommerceEdgeCases:
    @pytest.fixture
    def setup_data(self, api_client):
        user1 = User.objects.create_user(username='user1', email='user1@test.com', password='password123')
        user2 = User.objects.create_user(username='user2', email='user2@test.com', password='password123')
        
        collection = Collection.objects.create(title="Accessories")
        product_active = Product.objects.create(title="Active Item", unit_price=100.0, inventory=10, collection=collection)
        product_empty = Product.objects.create(title="Empty Item", unit_price=50.0, inventory=0, collection=collection)
        
        cart = Cart.objects.create()
        CartItem.objects.create(cart=cart, product=product_active, quantity=2)
        
        return {
            'user1': user1,
            'user2': user2,
            'collection': collection,
            'product_active': product_active,
            'product_empty': product_empty,
            'cart': cart,
            'client': api_client
        }

    def test_add_zero_quantity_to_cart_returns_400(self, setup_data):
        client = setup_data['client']
        cart_id = setup_data['cart'].id
        product_id = setup_data['product_active'].id
        
        response = client.post(f'/store/carts/{cart_id}/items/', {'product_id': product_id, 'quantity': 0})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_negative_quantity_to_cart_returns_400(self, setup_data):
        client = setup_data['client']
        cart_id = setup_data['cart'].id
        product_id = setup_data['product_active'].id
        
        response = client.post(f'/store/carts/{cart_id}/items/', {'product_id': product_id, 'quantity': -5})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_out_of_stock_item_to_cart_returns_400(self, setup_data):
        client = setup_data['client']
        cart_id = setup_data['cart'].id
        product_id = setup_data['product_empty'].id
        
        response = client.post(f'/store/carts/{cart_id}/items/', {'product_id': product_id, 'quantity': 1})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_more_quantity_than_inventory_returns_400(self, setup_data):
        client = setup_data['client']
        cart_id = setup_data['cart'].id
        product_id = setup_data['product_active'].id
        
        response = client.post(f'/store/carts/{cart_id}/items/', {'product_id': product_id, 'quantity': 9999})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_non_existent_product_returns_404(self, setup_data):
        client = setup_data['client']
        response = client.get('/store/products/999999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_non_existent_collection_returns_404(self, setup_data):
        client = setup_data['client']
        response = client.get('/store/collections/999999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_filter_products_by_invalid_collection_returns_empty_or_400(self, setup_data):
        client = setup_data['client']
        response = client.get('/store/products/?collection_id=999999')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_with_missing_password_returns_400(self, setup_data):
        client = setup_data['client']
        response = client.post('/auth/jwt/create/', {'username': 'user1'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_with_existing_email_returns_400(self, setup_data):
        client = setup_data['client']
        payload = {
            'username': 'newuser123',
            'email': setup_data['user1'].email, 
            'password': 'Password123!'
        }
        response = client.post('/auth/users/', payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_with_weak_password_returns_400(self, setup_data):
        client = setup_data['client']
        payload = {
            'username': 'weakuser',
            'email': 'weak@example.com',
            'password': '123' 
        }
        response = client.post('/auth/users/', payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_order_creation_with_missing_billing_fields_returns_400(self, setup_data):
        client = setup_data['client']
        user = setup_data['user1']
        cart_id = setup_data['cart'].id
        
        client.force_authenticate(user=user)
        payload = {
            'cart_id': cart_id,
            'first_name': 'John'
        }
        response = client.post('/store/orders/', payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST