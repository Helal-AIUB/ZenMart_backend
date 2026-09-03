import csv
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import generics
from .models import Article, ArticleCategory, Notification, Coupon
from store.permissions import IsAdminOrReadOnly
from rest_framework.views import APIView
from .filters import ProductFilter
from .pagination import DefaultPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import status
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from .models import Cart, CartItem, Customer, Order, OrderItem, Product, Collection, ProductImage, Review, StoreSettings
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, F
from django.db.models.functions import TruncDate
from .serializers import ArticleSerializer, ArticleCategorySerializer, NotificationSerializer, CouponSerializer, CouponValidateSerializer
from .serializers import AddCartItemSerializer, CartItemSerializer, CartSerializer, CreateOrderSerializer, CustomerSerializer, OrderSerializer, UpdateOrderItemSerializer, ProductImageSerializer, ProductSerializer, CollectionSerializer, ReviewSerializer, UpdateCartItemSerializer, UpdateOrderSerializer, StoreSettingsSerializer, OrderItemSerializer

class ProductViewSet(ModelViewSet):  
    # Optimized: Fetches related collection and pre-fetches all images in just 2 queries
    queryset = Product.objects.select_related('collection').prefetch_related('images').all()
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    pagination_class = DefaultPagination
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'last_update']

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
         if(OrderItem.objects.filter(product_id = kwargs['pk']).count()>0):
              return Response(
                                  {'ERROR': 'Product can not be deleted because it is associated with an order item'},
                                  status=status.HTTP_405_METHOD_NOT_ALLOWED
                              )
         return super().destroy(request, *args, **kwargs)


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(products_count=Count('product')).all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        collection = self.get_object() 
        
        if collection.product.count() > 0:
            return Response(
                {'error': 'Collection cannot be deleted because it includes one or more products.'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
            
        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(product_id = self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}


class CartViewSet(CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    # Optimized: Fetches cart items, their products, and product images efficiently
    queryset = Cart.objects.prefetch_related('items__product__images').all()
    serializer_class = CartSerializer

class CartItemViewSet(ModelViewSet):

    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return AddCartItemSerializer
        elif self.request.method == 'PATCH':
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}

    def get_queryset(self):
        # Optimized: Added prefetch_related for images
        return CartItem.objects \
                    .filter(cart_id = self.kwargs['cart_pk']) \
                    .select_related('product') \
                    .prefetch_related('product__images')

class CustomerViewSet(ModelViewSet):
    # Optimized: Fetches the associated user model instantly
    queryset = Customer.objects.select_related('user').all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods = ['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        customer = Customer.objects.select_related('user').get(user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data = request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    
    def get_permissions(self):
        if self.request.method in ['PATCH', 'DELETE']:
            if self.action == 'verify_payment':
                return [IsAuthenticated()]
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(data=request.data, context = {'user_id' : self.request.user.id})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)

        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        elif self.request.method == 'PATCH':
            return UpdateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        
        # Highly Optimized: Joins customer and user, prefetches all order items and their products
        queryset = Order.objects.select_related('customer', 'customer__user').prefetch_related('items__product')

        if user.is_staff:
            return queryset.all()

        # Optimized: Filters directly using relation traversal, saves 1 extra database hit
        return queryset.filter(customer__user_id=user.id)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def verify_payment(self, request, pk=None):
        order = self.get_object()
        
        if not request.user.is_staff and order.customer.user_id != request.user.id:
            return Response({'error': 'You do not have permission to verify this order.'}, status=status.HTTP_403_FORBIDDEN)

        transaction_id = request.data.get('transaction_id')
        if not transaction_id:
            return Response({'error': 'Transaction ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        order.transaction_id = transaction_id
        order.save()
        
        return Response({
            'status': 'Payment verification submitted successfully.', 
            'transaction_id': transaction_id
        })
        
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def add_item(self, request, pk=None):
        order = self.get_object()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        if not product_id:
            return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, pk=product_id)

        if OrderItem.objects.filter(order=order, product=product).exists():
            return Response({'error': 'Product is already in the order'}, status=status.HTTP_400_BAD_REQUEST)

        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            unit_price=product.unit_price,
            quantity=quantity
        )

        serializer = OrderItemSerializer(order_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ProductImageViewSet(ModelViewSet):
    serializer_class = ProductImageSerializer

    def get_serializer_context(self):
        return {'product_id' : self.kwargs['product_pk']}

    def get_queryset(self):
        return ProductImage.objects.filter(product_id = self.kwargs['product_pk'])
    

class DashboardStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_products = Product.objects.count()
        low_stock_alerts = Product.objects.filter(inventory__lt=10).count()
        total_orders = Order.objects.count()
        total_customers = Customer.objects.count()

        return Response({
            "total_products": total_products,
            "low_stock_alerts": low_stock_alerts,
            "total_orders": total_orders,
            "total_customers": total_customers,
        })
        
@api_view(['GET'])
@permission_classes([IsAdminUser])
def revenue_analytics(request):
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    sales_data = (
        OrderItem.objects
        .filter(order__placed_at__gte=thirty_days_ago)
        .exclude(order__delivery_status='Canceled')
        .annotate(date=TruncDate('order__placed_at'))
        .values('date')
        .annotate(revenue=Sum(F('unit_price') * F('quantity')))
        .order_by('date')
    )
    
    formatted_data = []
    for item in sales_data:
        formatted_data.append({
            "date": item['date'].strftime("%b %d"), 
            "revenue": float(item['revenue'])
        })
        
    return Response(formatted_data)

class OrderItemViewSet(ModelViewSet):
    http_method_names = ['patch', 'delete']
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        return UpdateOrderItemSerializer

    def get_queryset(self):
        # Optimized: Preloads the product for fast response
        return OrderItem.objects.filter(order_id=self.kwargs['order_pk']).select_related('product')


class StoreSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = StoreSettingsSerializer

    def get_object(self):
        return StoreSettings.load()


# class StoreSettingsView(APIView):
    
#     def get_permissions(self):
#         if self.request.method == 'GET':
#             return [AllowAny()]
#         return [IsAdminUser()]

#     def get(self, request):
#         settings = StoreSettings.load()
#         serializer = StoreSettingsSerializer(settings)
#         return Response(serializer.data)

#     def patch(self, request):
#         settings = StoreSettings.load()
#         serializer = StoreSettingsSerializer(settings, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class ArticleCategoryViewSet(ModelViewSet):
    queryset = ArticleCategory.objects.all()
    serializer_class = ArticleCategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class ArticleViewSet(ModelViewSet):
    queryset = Article.objects.select_related('category').prefetch_related('related_products').all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'category', 'slug']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['created_at', 'views']
    
    # Custom API to increment view count
    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def add_view(self, request, pk=None):
        article = self.get_object()
        article.views += 1
        article.save()
        return Response({'status': 'view added', 'views': article.views})
    
class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAdminUser]  

    @action(detail=False, methods=['GET'])
    def unread_count(self, request):
        count = Notification.objects.filter(is_read=False).count()
        return Response({'unread_count': count})
        
    @action(detail=True, methods=['PATCH'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
        
    @action(detail=False, methods=['POST'])
    def mark_all_read(self, request):
        Notification.objects.filter(is_read=False).update(is_read=True)
        return Response({'status': 'all notifications marked as read'})
    
class CouponViewSet(ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    
    def get_permissions(self):
        if self.action == 'validate':
            return [AllowAny()]
        return [IsAdminUser()]

    @action(detail=False, methods=['post'])
    def validate(self, request):
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({
            "status": "success",
            "message": "Coupon applied successfully!",
            "discount_amount": serializer.validated_data['discount'],
            "coupon_code": serializer.validated_data['coupon'].code
        }, status=status.HTTP_200_OK)
        
