import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import ValidationError
from store.models import Coupon, Cart, CartItem, Product, Collection
from store.serializers import CouponValidateSerializer
from model_bakery import baker

@pytest.mark.django_db
class TestCouponValidation:
    
    @pytest.fixture
    def setup_cart_data(self):
        """creating a fake cart and adding 2 products of 100 tk"""
        cart = baker.make(Cart)
        product = baker.make(Product, unit_price=100)
        baker.make(CartItem, cart=cart, product=product, quantity=2)
        return cart, product

    def test_valid_global_percentage_coupon(self, setup_cart_data):
        cart, _ = setup_cart_data  
        
        baker.make(
            Coupon,
            code="WINTER20",
            discount_type=Coupon.DISCOUNT_TYPE_PERCENTAGE,
            discount_amount=20,  # 20% discount
            is_global=True,
            active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=1),
            min_purchase_amount=100
        )

        serializer = CouponValidateSerializer(data={'code': 'WINTER20', 'cart_id': cart.id})
        
        assert serializer.is_valid() == True
        # 20% of 200 = 40 tk discount
        assert serializer.validated_data['discount'] == 40

    def test_expired_coupon_raises_error(self, setup_cart_data):
        """test: after expired coupon whether error shows or not"""
        cart, _ = setup_cart_data
        
        baker.make(
            Coupon,
            code="EXPIRED",
            active=True,
            valid_from=timezone.now() - timedelta(days=10),
            valid_to=timezone.now() - timedelta(days=1) 
        )
        
        serializer = CouponValidateSerializer(data={'code': 'EXPIRED', 'cart_id': cart.id})
        
        assert serializer.is_valid() == False
        assert "expired or not yet valid" in str(serializer.errors['code'][0])

    def test_minimum_purchase_amount_not_met(self, setup_cart_data):
        """test: Whether error shows or not if purchased amount not met"""
        cart, _ = setup_cart_data  
        
        baker.make(
            Coupon,
            code="MIN500",
            is_global=True,
            active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=1),
            min_purchase_amount=500  # must have to buy at least 500 tk
        )
        
        serializer = CouponValidateSerializer(data={'code': 'MIN500', 'cart_id': cart.id})
        
        assert serializer.is_valid() == False
        assert "Minimum eligible purchase amount" in str(serializer.errors['code'][0])

    def test_usage_limit_reached(self, setup_cart_data):
        """test: when limit reached whether coupon stop or not"""
        cart, _ = setup_cart_data
        
        baker.make(
            Coupon,
            code="LIMITREACHED",
            is_global=True,
            active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=1),
            usage_limit=10,
            used_count=10  # already 10 times used
        )
        
        serializer = CouponValidateSerializer(data={'code': 'LIMITREACHED', 'cart_id': cart.id})
        
        assert serializer.is_valid() == False
        assert "usage limit has been reached" in str(serializer.errors['code'][0])
        
    def test_specific_product_coupon(self, setup_cart_data):
        cart, product1 = setup_cart_data  
        
        product2 = baker.make(Product, unit_price=300)
        baker.make(CartItem, cart=cart, product=product2, quantity=1)
        
        coupon = baker.make(
            Coupon,
            code="SPECIFIC10",
            discount_type=Coupon.DISCOUNT_TYPE_PERCENTAGE,
            discount_amount=10, 
            is_global=False,
            active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=1)
        )
        coupon.applicable_products.add(product1)
        
        serializer = CouponValidateSerializer(data={'code': 'SPECIFIC10', 'cart_id': cart.id})
        
        assert serializer.is_valid() == True
        assert serializer.validated_data['discount'] == 20

    def test_coupon_not_applicable_to_cart_items(self, setup_cart_data):
        cart, _ = setup_cart_data 
        
        other_product = baker.make(Product, unit_price=500)
        
        coupon = baker.make(
            Coupon,
            code="NOTFORYOU",
            is_global=False,
            active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=1)
        )
        coupon.applicable_products.add(other_product)
        
        serializer = CouponValidateSerializer(data={'code': 'NOTFORYOU', 'cart_id': cart.id})
        
        assert serializer.is_valid() == False
        assert "not applicable" in str(serializer.errors['code'][0])
    
    