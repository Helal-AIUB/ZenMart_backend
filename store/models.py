from django.conf import settings
from django.contrib import admin
from django.db import models
from uuid import uuid4
from django.utils.text import slugify
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
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.inventory < 10:
            unread_alert_exists = Notification.objects.filter(
                notification_type=Notification.TYPE_STOCK,
                product=self,
                is_read=False
            ).exists()
            
            if not unread_alert_exists:
                Notification.objects.create(
                    notification_type=Notification.TYPE_STOCK,
                    title="Low Stock Alert",
                    message=f"{self.title} is running low on stock ({self.inventory} left).",
                    product=self
                )

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


class Coupon(models.Model):
    DISCOUNT_TYPE_PERCENTAGE = 'percentage'
    DISCOUNT_TYPE_FIXED = 'fixed'
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_TYPE_PERCENTAGE, 'Percentage (%)'),
        (DISCOUNT_TYPE_FIXED, 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="e.g. PETORA20, WINTER50")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default=DISCOUNT_TYPE_PERCENTAGE)
    discount_amount = models.DecimalField(max_digits=6, decimal_places=2)
    min_purchase_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Minimum cart value required")
    
    # 🟢 Coupon Scope (All, Specific Collections, or Specific Products)
    is_global = models.BooleanField(default=True, help_text="If True, applies to all products.")
    applicable_collections = models.ManyToManyField(Collection, blank=True, related_name='coupons')
    applicable_products = models.ManyToManyField(Product, blank=True, related_name='coupons')

    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of times this coupon can be used globally")
    used_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code
        
    class Meta:
        ordering = ['-valid_to']


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
    
    PAYMENT_METHOD_COD = 'COD'
    PAYMENT_METHOD_BKASH = 'bKash'
    PAYMENT_METHOD_NAGAD = 'Nagad'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_COD, 'Cash on Delivery'),
        (PAYMENT_METHOD_BKASH, 'bKash'),
        (PAYMENT_METHOD_NAGAD, 'Nagad'),
    ]
 
    placed_at = models.DateTimeField(auto_now_add=True) 
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING) 
    
    # New Field for Tracking
    delivery_status = models.CharField(max_length=50, choices=DELIVERY_STATUS_CHOICES, default=DELIVERY_STATUS_PLACED) 
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_METHOD_COD)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Order Specific Shipping Address
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    zip_code = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    delivery_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT) 
    
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    discount_amount = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
 
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

class StoreSettings(models.Model):
    store_name = models.CharField(max_length=255, default="Petora BD")
    support_email = models.EmailField(default="support@petorabd.com")
    contact_phone = models.CharField(max_length=20, blank=True, help_text="hotline number")
    address = models.TextField(blank=True)
    delivery_charge_inside = models.DecimalField(max_digits=6, decimal_places=2, default=60.00)
    delivery_charge_outside = models.DecimalField(max_digits=6, decimal_places=2, default=120.00)
    currency_symbol = models.CharField(max_length=5, default="৳", help_text="Ex: $, ৳, €, £")

    short_description = models.TextField(blank=True, default="Your trusted partner for premium pet care, food, and accessories.", help_text="লোগোর নিচে দেখানোর জন্য শর্ট টেক্সট")
    business_hours = models.CharField(max_length=255, blank=True, default="9:00 AM - 10:00 PM (Everyday)")
    
    facebook_link = models.URLField(blank=True, help_text="Facebook Page URL")
    instagram_link = models.URLField(blank=True, help_text="Instagram Profile URL")
    youtube_link = models.URLField(blank=True, help_text="YouTube Channel URL")

    def save(self, *args, **kwargs):
        if not self.pk and StoreSettings.objects.exists():
            return 
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
        
    class Meta:
        verbose_name = "Store Setting"
        verbose_name_plural = "Store Settings"
    

class ArticleCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Article(models.Model):
    STATUS_PUBLISHED = 'Published'
    STATUS_DRAFT = 'Draft'
    STATUS_SCHEDULED = 'Scheduled'
    
    STATUS_CHOICES = [
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SCHEDULED, 'Scheduled'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    excerpt = models.TextField(max_length=500, help_text="Short summary for the card view")
    content = models.TextField(help_text="Full HTML or Markdown content") # এখানে আমরা পরে রিচ-টেক্সট এডিটর কানেক্ট করব
    
    category = models.ForeignKey(ArticleCategory, on_delete=models.SET_NULL, null=True, related_name='articles')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    
    image = models.ImageField(upload_to='articles/images/', null=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    
    # SEO Fields
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Link to products (For smart tagging later)
    related_products = models.ManyToManyField('Product', blank=True, related_name='featured_in_articles')

    def save(self, *args, **kwargs):
        if self.title and (not self.slug or self.slug == ""):
            original_slug = slugify(self.title)
            
            if not original_slug:
                original_slug = "article"
                
            slug = original_slug
            counter = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
        
class Notification(models.Model):
    TYPE_ORDER = 'order'
    TYPE_STOCK = 'stock'
    
    TYPE_CHOICES = [
        (TYPE_ORDER, 'New Order'),
        (TYPE_STOCK, 'Low Stock Alert'),
    ]
    
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional references (to redirect admin directly to the specific item)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"
    
