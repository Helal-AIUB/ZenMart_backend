from django.urls import path 
from rest_framework_nested import routers
from . import views 
# from pprint import pprint



router = routers.DefaultRouter()
router.register('products', views.ProductViewSet, basename='products')
router.register('collections', views.CollectionViewSet)
router.register('carts', views.CartViewSet)
router.register('customers', views.CustomerViewSet)
router.register('orders', views.OrderViewSet, basename='orders')
router.register('article-categories', views.ArticleCategoryViewSet, basename='article-categories')
router.register('articles', views.ArticleViewSet, basename='articles')

# pprint(router.urls)

products_router = routers.NestedDefaultRouter(router, 'products', lookup = 'product')
products_router.register('reviews', views.ReviewViewSet, basename = 'product-reviews')
products_router.register('images', views.ProductImageViewSet, basename= 'product-images')

carts_router = routers.NestedDefaultRouter(router, 'carts', lookup = 'cart')
carts_router.register('items', views.CartItemViewSet, basename = 'cart-items-detail')

orders_router = routers.NestedDefaultRouter(router, 'orders', lookup='order')
orders_router.register('items', views.OrderItemViewSet, basename='order-items-detail')

urlpatterns = router.urls + products_router.urls + carts_router.urls

urlpatterns = [
    path('dashboard-stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('revenue-analytics/', views.revenue_analytics, name='revenue-analytics'),
    path('settings/', views.StoreSettingsView.as_view(), name='store-settings'),
] + router.urls + products_router.urls + carts_router.urls + orders_router.urls
