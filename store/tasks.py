from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, F
from django.db.models.functions import TruncDate
from .models import Product, Order, Customer, OrderItem

@shared_task
def calculate_dashboard_stats():
    # 1. Calculate General Dashboard Stats
    stats_data = {
        "total_products": Product.objects.count(),
        "low_stock_alerts": Product.objects.filter(inventory__lt=10).count(),
        "total_orders": Order.objects.count(),
        "total_customers": Customer.objects.count(),
    }
    
    # 2. Calculate Revenue Analytics for the last 30 days
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

    # Save both data sets to Redis Cache for 15 minutes (900 seconds)
    # Keeping it 15 mins ensures data doesn't expire before the next 10-min celery beat cycle
    cache.set('admin_dashboard_stats', stats_data, timeout=900)
    cache.set('admin_revenue_analytics', formatted_data, timeout=900)

    return "Dashboard stats successfully calculated and cached!"