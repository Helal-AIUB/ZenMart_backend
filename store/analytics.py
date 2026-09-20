from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest, RunRealtimeReportRequest, OrderBy
from django.conf import settings
from django.core.cache import cache
import datetime

def fetch_ga4_dashboard_metrics():
    # Cache key change kora hoyeche jate instant update hoi
    cache_key = 'ga4_admin_dashboard_v2' 
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    try:
        client = BetaAnalyticsDataClient()
        property_id = f"properties/{settings.GA4_PROPERTY_ID}"

        # 1. Realtime Users
        realtime_req = RunRealtimeReportRequest(
            property=property_id,
            metrics=[Metric(name="activeUsers")]
        )
        realtime_res = client.run_realtime_report(realtime_req)
        active_users = realtime_res.rows[0].metric_values[0].value if realtime_res.rows else 0

        # 2. Top Pages & Totals (Last 30 Days)
        report_req = RunReportRequest(
            property=property_id,
            dimensions=[Dimension(name="pageTitle")],
            metrics=[Metric(name="screenPageViews"), Metric(name="totalUsers")],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            limit=10  
        )
        report_res = client.run_report(report_req)

        top_pages = []
        total_views = 0
        total_users = 0

        for row in report_res.rows:
            title = row.dimension_values[0].value
            views = int(row.metric_values[0].value)
            users = int(row.metric_values[1].value)
            
            top_pages.append({
                "title": title,
                "views": views, 
                "users": users
            })
            total_views += views
            total_users += users

        # 3. Traffic Trend (Day by Day - Last 30 Days)
        trend_req = RunReportRequest(
            property=property_id,
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="activeUsers"), Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
            order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))]
        )
        trend_res = client.run_report(trend_req)

        traffic_trend = []
        for row in trend_res.rows:
            date_str = row.dimension_values[0].value
            date_obj = datetime.datetime.strptime(date_str, "%Y%m%d")
            formatted_date = date_obj.strftime("%b %d")

            traffic_trend.append({
                "name": formatted_date,
                "users": int(row.metric_values[0].value),
                "pageViews": int(row.metric_values[1].value)
            })

        data = {
            "realtime_active_users": int(active_users),
            "last_30_days": {
                "total_views": total_views,
                "total_users": total_users,
            },
            "top_pages": top_pages,
            "traffic_trend": traffic_trend
        }

        cache.set(cache_key, data, timeout=300)
        return data

    except Exception as e:
        print(f"GA4 Error: {e}")
        return {}