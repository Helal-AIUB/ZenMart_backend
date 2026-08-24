from django.conf import settings
from django.contrib import admin
from django.db import models
from uuid import uuid4
from django.core.validators import MinValueValidator, FileExtensionValidator

from store.validators import validate_file_size

class Collection(models.Model):
    title = models.CharField(max_length=255)
    featured_product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, related_name='+')

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ['title']


class Promotion(models.Model):
    description = models.CharField(max_length=255)
    discount = models.FloatField()

class Product(models.Model):
    # sku = models.CharField(max_length=10, primary_key=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(null=True, blank = True)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2, validators = [MinValueValidator(1)])
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    last_update = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT)
    promotions =  models.ManyToManyField(Promotion, blank = True)

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ['title']

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to = 'store/images', validators = [validate_file_size])


class Customer(models.Model):
    MEMBERSHIP_BRONZE = 'B'
    MEMBERSHIP_SILVER = 'S'
    MEMBERSHIP_GOLD = 'G'
    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_BRONZE, 'Bronze'),
        (MEMBERSHIP_SILVER, 'Silver'),
        (MEMBERSHIP_GOLD, 'Gold'),
    ]
    phone = models.CharField(max_length=255)
    dob = models.DateField(null=True)
    membership = models.CharField(max_length=30, choices = MEMBERSHIP_CHOICES, default='B')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    @admin.display(ordering = 'user__first_name')
    def first_name(self):
        return self.user.first_name
    
    @admin.display(ordering = 'user__last_name')
    def last_name(self):
            return self.user.last_name

    class Meta:
        # db_table = 'store_customers'
        # indexes = [
        #     models.Index(fields = ['last_name','first_name'])
        # ]
        ordering = ['user__first_name', 'user__last_name']


class Order(models.Model): 
    # Payment Status
    PAYMENT_STATUS_PENDING = 'P' 
    PAYMENT_STATUS_COMPLETE = 'C' 
    PAYMENT_STATUS_FAILED = 'F' 
    PAYMENT_STATUS_CHOICES = [ 
        (PAYMENT_STATUS_PENDING, 'Pending'), 
        (PAYMENT_STATUS_COMPLETE, 'Complete'), 
        (PAYMENT_STATUS_FAILED, 'Failed'), 
    ] 

    # Delivery Tracking Status (NEW)
    DELIVERY_STATUS_PLACED = 'Placed'
    DELIVERY_STATUS_PROCESSING = 'Processing'
    DELIVERY_STATUS_SHIPPED = 'Shipped'
    DELIVERY_STATUS_DELIVERED = 'Delivered'
    DELIVERY_STATUS_CANCELED = 'Canceled'
    
    DELIVERY_STATUS_CHOICES = [
        (DELIVERY_STATUS_PLACED, 'Placed'),
        (DELIVERY_STATUS_PROCESSING, 'Processing'),
        (DELIVERY_STATUS_SHIPPED, 'Shipped'),
        (DELIVERY_STATUS_DELIVERED, 'Delivered'),
        (DELIVERY_STATUS_CANCELED, 'Canceled'),
    ]
 
    placed_at = models.DateTimeField(auto_now_add=True) 
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING) 
    
    # New Field for Tracking
    delivery_status = models.CharField(max_length=50, choices=DELIVERY_STATUS_CHOICES, default=DELIVERY_STATUS_PLACED) 
    
    # Order Specific Shipping Address
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    zip_code = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT) 
 
    class Meta: 
        permissions = [ 
            ('cancel_order', 'Can cancel order') 
        ]

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name = 'items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name = 'orderitems')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)

class Address(models.Model):
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    zip = models.CharField(max_length=255)

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(
        validators = [MinValueValidator(1)]
    )

    class Meta:
        unique_together = [['cart','product']]

class Review(models.Model):
    product =  models.ForeignKey(Product, on_delete = models.CASCADE, related_name = 'reviews' )
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add = True)
