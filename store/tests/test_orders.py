import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from store.models import Product, Collection, Cart, CartItem, Order

User = get_user_model()

@pytest.mark.django_db
class TestOrdersAPI:
    @pytest.fixture
    def setup_data(self, api_client):
        user = User.objects.create_user(username='testuser', password='testpassword123')
        collection = Collection.objects.create(title="Pet Accessories")
        product = Product.objects.create(
            title="Dog Collar", 
            unit_price=15.00, 
            inventory=20, 
            collection=collection
        )
        cart = Cart.objects.create()
        CartItem.objects.create(cart=cart, product=product, quantity=2)
        
        return {
            'user': user,
            'product': product,
            'cart': cart,
            'client': api_client
        }

    def test_anonymous_user_cannot_create_order(self, setup_data):
        client = setup_data['client']
        cart_id = setup_data['cart'].id
        
        response = client.post('/store/orders/', {'cart_id': cart_id})
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_order_returns_200(self, setup_data):
        client = setup_data['client']
        user = setup_data['user']
        cart = setup_data['cart']
        
        client.force_authenticate(user=user)
        
        payload = {
            'cart_id': cart.id,
            'first_name': 'John',
            'last_name': 'Doe',
            'street': '123 Pet Street',
            'city': 'Dhaka',
            'zip_code': '1200',
            'phone': '+8801700000000',
            'delivery_charge': 60.00
        }
        
        response = client.post('/store/orders/', payload)
        
        assert response.status_code == status.HTTP_200_OK
        assert Order.objects.filter(customer__user=user).exists()
        assert not Cart.objects.filter(id=cart.id).exists()

    def test_create_order_with_empty_cart_returns_400(self, setup_data):
        client = setup_data['client']
        user = setup_data['user']
        empty_cart = Cart.objects.create()
        
        client.force_authenticate(user=user)
        
        payload = {
            'cart_id': empty_cart.id,
            'first_name': 'John',
            'last_name': 'Doe',
            'street': '123 Pet Street',
            'city': 'Dhaka',
            'zip_code': '1200',
            'phone': '+8801700000000',
            'delivery_charge': 60.00
        }
        
        response = client.post('/store/orders/', payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_order_with_invalid_cart_returns_400(self, setup_data):
        client = setup_data['client']
        user = setup_data['user']
        
        client.force_authenticate(user=user)
        import uuid
        invalid_cart_id = uuid.uuid4()
        
        payload = {
            'cart_id': invalid_cart_id,
            'first_name': 'John',
            'last_name': 'Doe',
            'street': '123 Pet Street',
            'city': 'Dhaka',
            'zip_code': '1200',
            'phone': '+8801700000000',
            'delivery_charge': 60.00
        }
        
        response = client.post('/store/orders/', payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_orders_returns_200(self, setup_data):
        client = setup_data['client']
        user = setup_data['user']
        
        client.force_authenticate(user=user)
        response = client.get('/store/orders/')
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list) or 'results' in response.data