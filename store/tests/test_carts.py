import pytest
from rest_framework import status
from store.models import Product, Collection, Cart, CartItem

@pytest.mark.django_db
class TestCartsAPI:
    def test_create_cart_returns_201(self, api_client):
        # API Testing & Business Logic: Ensuring cart generation works and returns a UUID
        response = api_client.post('/store/carts/')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data

    def test_get_cart_returns_200(self, api_client):
        # Unit/Integration Testing: Creating a cart in DB and fetching it via API
        cart = Cart.objects.create()
        
        response = api_client.get(f'/store/carts/{cart.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(cart.id)
        assert 'items' in response.data
        assert 'total_price' in response.data

@pytest.mark.django_db
class TestCartItemsAPI:
    @pytest.fixture
    def setup_data(self):
        # Setup common test data (Integration focus)
        collection = Collection.objects.create(title="Pet Supplies")
        product = Product.objects.create(
            title="Premium Dog Food", 
            unit_price=10.00, 
            inventory=50, 
            collection=collection
        )
        cart = Cart.objects.create()
        return {'product': product, 'cart': cart}

    def test_add_item_to_cart_returns_201(self, api_client, setup_data):
        # API & Integration Testing: Validating POST method for cart items
        cart_id = setup_data['cart'].id
        product_id = setup_data['product'].id
        
        response = api_client.post(f'/store/carts/{cart_id}/items/', {
            'product_id': product_id,
            'quantity': 2
        })
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['quantity'] == 2

    def test_update_item_quantity_returns_200(self, api_client, setup_data):
        # Business Logic Testing: Verifying quantity modifications
        cart = setup_data['cart']
        product = setup_data['product']
        cart_item = CartItem.objects.create(cart=cart, product=product, quantity=1)
        
        response = api_client.patch(f'/store/carts/{cart.id}/items/{cart_item.id}/', {
            'quantity': 5
        })
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['quantity'] == 5

    def test_delete_cart_item_returns_204(self, api_client, setup_data):
        # API Testing: Verifying correct status code for deletion and DB sync
        cart = setup_data['cart']
        product = setup_data['product']
        cart_item = CartItem.objects.create(cart=cart, product=product, quantity=1)
        
        response = api_client.delete(f'/store/carts/{cart.id}/items/{cart_item.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CartItem.objects.filter(id=cart_item.id).exists()

    def test_add_invalid_product_returns_400(self, api_client, setup_data):
        # Business Logic / Validation Testing: Handling bad inputs
        cart_id = setup_data['cart'].id
        
        response = api_client.post(f'/store/carts/{cart_id}/items/', {
            'product_id': 999999,  # Non-existent product
            'quantity': 1
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST