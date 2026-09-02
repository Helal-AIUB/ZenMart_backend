from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from django.utils import timezone
from .signals import order_created
from .models import Article, ArticleCategory, Notification, Coupon
from .models import Cart, CartItem, Customer, Order, OrderItem, Product, Collection, ProductImage, Review, StoreSettings
from core.serializers import UserSerializer

class CollectionSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Collection
        fields = ['id', 'title', 'products_count']
        read_only_fields = ['products_count']

class ProductImageSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        product_id = self.context['product_id']
        return ProductImage.objects.create(product_id = product_id, **validated_data)
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product            # Model serializer
        fields = ['id', 'title', 'description', 'slug', 'inventory', 'unit_price', 'collection', 'images']

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)
    

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'date', 'name', 'description']

    def create(self, validated_data):
        product_id = self.context['product_id']
        return Review.objects.create(product_id = product_id, **validated_data)

class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']

class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.product.unit_price

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']

class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only = True)
    items = CartItemSerializer(many = True, read_only = True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart):
        return sum([item.quantity * item.product.unit_price for item in cart.items.all()])
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'

class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)
    cart_id = serializers.UUIDField()

    def validate(self, attrs):
        code = attrs.get('code')
        cart_id = attrs.get('cart_id')
        now = timezone.now()

        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({"code": "Invalid coupon code."})

        if not coupon.active:
            raise serializers.ValidationError({"code": "This coupon is no longer active."})
        
        if not (coupon.valid_from <= now <= coupon.valid_to):
            raise serializers.ValidationError({"code": "This coupon is expired or not yet valid."})
        
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            raise serializers.ValidationError({"code": "This coupon usage limit has been reached."})

        # Validate against cart items
        try:
            cart = Cart.objects.prefetch_related('items__product__collection').get(id=cart_id)
        except Cart.DoesNotExist:
            raise serializers.ValidationError({"cart_id": "Invalid cart ID."})

        cart_items = cart.items.all()
        if not cart_items:
            raise serializers.ValidationError({"cart_id": "Your cart is empty."})

        # Calculate eligible subtotal (only items that match the coupon's scope)
        eligible_subtotal = 0
        for item in cart_items:
            product = item.product
            is_eligible = False
            
            if coupon.is_global:
                is_eligible = True
            elif coupon.applicable_products.filter(id=product.id).exists():
                is_eligible = True
            elif coupon.applicable_collections.filter(id=product.collection_id).exists():
                is_eligible = True
            
            if is_eligible:
                eligible_subtotal += (product.unit_price * item.quantity)

        if eligible_subtotal == 0:
            raise serializers.ValidationError({"code": "This coupon is not applicable to the items in your cart."})

        if eligible_subtotal < coupon.min_purchase_amount:
            raise serializers.ValidationError({"code": f"Minimum eligible purchase amount of ${coupon.min_purchase_amount} required."})

        # Calculate final discount
        discount = 0
        if coupon.discount_type == Coupon.DISCOUNT_TYPE_PERCENTAGE:
            discount = (eligible_subtotal * coupon.discount_amount) / 100
        else:
            discount = coupon.discount_amount
            # Ensure discount doesn't exceed the eligible subtotal
            if discount > eligible_subtotal:
                discount = eligible_subtotal 

        attrs['coupon'] = coupon
        attrs['discount'] = discount
        return attrs

class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('No Product with the given ID was found.')
        return value

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        try:
            cart_item = CartItem.objects.get(cart_id = cart_id, product_id = product_id)
            # update an existing item
            cart_item.quantity +=quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            # create a new item
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)
        return self.instance

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']

class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']

class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    user = UserSerializer(read_only=True)
    class Meta:
        model = Customer 
        fields = ['id', 'user_id', 'phone', 'dob', 'membership', 'user']

class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    class Meta:
        model = OrderItem 
        fields = ['id', 'product', 'unit_price', 'quantity']

class OrderSerializer(serializers.ModelSerializer): 
    items = OrderItemSerializer(many=True) 
    coupon_code = serializers.CharField(source='coupon.code', read_only=True) 
     
    class Meta: 
        model = Order 
        fields = ['id', 'customer', 'placed_at', 'payment_status', 'delivery_status', 
                  'first_name', 'last_name', 'street', 'city', 'zip_code', 'phone', 
                  'delivery_charge', 'payment_method', 'transaction_id', 'items', 
                  'coupon_code', 'discount_amount'] 
class UpdateOrderSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = Order 
        fields = ['payment_status', 'delivery_status']
        

class CreateOrderSerializer(serializers.Serializer): 
    cart_id = serializers.UUIDField() 
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    street = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=255)
    zip_code = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=255)
    delivery_charge = serializers.DecimalField(max_digits=6, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES, default=Order.PAYMENT_METHOD_COD)
    coupon_code = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_cart_id(self, cart_id):                                    
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError('No cart with the given ID was found.')
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('The cart is empty.')
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            customer = Customer.objects.get(user_id=self.context['user_id'])
            
            coupon_code = self.validated_data.get('coupon_code')
            applied_coupon = None
            discount_amount = 0

            if coupon_code:
                # Validate using the serializer we just made
                coupon_serializer = CouponValidateSerializer(data={'code': coupon_code, 'cart_id': cart_id})
                if coupon_serializer.is_valid():
                    applied_coupon = coupon_serializer.validated_data['coupon']
                    discount_amount = coupon_serializer.validated_data['discount']
                    applied_coupon.used_count += 1
                    applied_coupon.save()
            
            # Saving address when ordered
            order = Order.objects.create(
                customer=customer,
                first_name=self.validated_data['first_name'],
                last_name=self.validated_data['last_name'],
                street=self.validated_data['street'],
                city=self.validated_data['city'],
                zip_code=self.validated_data['zip_code'],
                phone=self.validated_data['phone'],
                delivery_charge=self.validated_data['delivery_charge'],
                payment_method=self.validated_data.get('payment_method', Order.PAYMENT_METHOD_COD),
                coupon=applied_coupon,
                discount_amount=discount_amount
            )

            cart_items = CartItem.objects.select_related('product').filter(cart_id=cart_id)
            order_items = [ 
                OrderItem(
                    order=order,
                    product=item.product,
                    unit_price=item.product.unit_price,
                    quantity=item.quantity,
                ) for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items)
            Cart.objects.filter(pk=cart_id).delete()
            
            Notification.objects.create(
                notification_type=Notification.TYPE_ORDER,
                title=f"New Order #{order.id}",
                message=f"{order.first_name} {order.last_name} has placed a new order.",
                order=order
            )
            order_created.send_robust(self.__class__, order=order)

            return order


class UpdateOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['quantity']
        
        
class StoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreSettings
        fields = '__all__'



class ArticleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleCategory
        fields = ['id', 'name', 'slug']

class ArticleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt', 'content', 'category', 'category_name', 
            'status', 'image', 'views', 'meta_title', 'meta_description', 
            'created_at', 'updated_at', 'related_products'
        ]
        read_only_fields = ['slug', 'views', 'created_at', 'updated_at']
        
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'created_at', 'order', 'product']