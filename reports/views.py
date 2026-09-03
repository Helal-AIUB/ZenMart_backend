import csv
import traceback
from xhtml2pdf import pisa
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse
from rest_framework.decorators import api_view

from store.models import Order, Product, Customer


@api_view(['GET'])
# @permission_classes([IsAdminUser]) 
def export_data_api(request):
    try:
        report_type = request.query_params.get('type', 'sales')
        date_range = request.query_params.get('range', '30')
        file_format = request.query_params.get('file_type', 'csv')

        now = timezone.now()
        start_date = None
        
        if date_range and date_range.lower() != 'all':
            try:
                days = int(date_range)
                start_date = now - timedelta(days=days)
            except ValueError:
                pass 

        columns = []
        data_rows = []

        # 1. INVENTORY & STOCK REPORT
        if report_type == 'inventory':
            columns = ['Product ID', 'Product Name', 'Category', 'Unit Price', 'Current Stock', 'Stock Status']
            products = Product.objects.select_related('collection').all()
            if start_date: products = products.filter(last_update__gte=start_date)
                
            for p in products:
                cat_name = p.collection.title if hasattr(p, 'collection') and p.collection else 'Uncategorized'
                if p.inventory == 0: stock_status = "Out of Stock"
                elif p.inventory < 10: stock_status = "Low Stock"
                else: stock_status = "In Stock"
                    
                data_rows.append([str(p.id), p.title, cat_name, f"${p.unit_price:.2f}", str(p.inventory), stock_status])

        # 2. ORDER FULFILLMENT REPORT
        elif report_type == 'orders':
            columns = ['Order ID', 'Date', 'Customer Name', 'Total Items', 'Payment Status']
            orders = Order.objects.select_related('customer', 'customer__user').prefetch_related('items').all()
            if start_date: orders = orders.filter(placed_at__gte=start_date)
                
            for o in orders:
                customer_name = f"{o.customer.user.first_name} {o.customer.user.last_name}".strip() if hasattr(o.customer, 'user') and o.customer.user else "Guest"
                total_items = sum([item.quantity for item in o.items.all()])
                data_rows.append([str(o.id), o.placed_at.strftime("%b %d, %Y"), customer_name or "Unknown User", str(total_items), o.payment_status])

        # 3. CUSTOMER INSIGHTS REPORT
        elif report_type == 'customers':
            columns = ['Customer ID', 'Name', 'Email', 'Phone', 'Total Orders', 'Total Spent']
            customers = Customer.objects.select_related('user').prefetch_related('order_set__items').all()
            
            for c in customers:
                name = f"{c.user.first_name} {c.user.last_name}".strip() if hasattr(c, 'user') and c.user else "Unknown"
                email = c.user.email if hasattr(c, 'user') and c.user else "N/A"
                phone = getattr(c, 'phone', 'N/A')
                
                user_orders = c.order_set.filter(placed_at__gte=start_date) if start_date else c.order_set.all()
                total_orders = user_orders.count()
                
                if start_date and total_orders == 0: continue
                    
                total_spent = sum(sum(item.quantity * item.unit_price for item in order.items.all()) for order in user_orders)
                data_rows.append([str(c.id), name or "Name Not Provided", email, phone, str(total_orders), f"${total_spent:.2f}"])

        # 4. SALES & REVENUE REPORT
        else:
            columns = ['Date', 'Order ID', 'Payment Status', 'Total Items', 'Revenue']
            orders = Order.objects.prefetch_related('items').all().order_by('-placed_at')
            if start_date: orders = orders.filter(placed_at__gte=start_date)
                
            for o in orders:
                total_items = sum([item.quantity for item in o.items.all()])
                revenue = sum([item.quantity * item.unit_price for item in o.items.all()])
                data_rows.append([o.placed_at.strftime("%b %d, %Y"), str(o.id), o.payment_status, str(total_items), f"${revenue:.2f}"])

        # ---------------------------------------------------------
        # EXPORT LOGIC: CSV
        # ---------------------------------------------------------
        if file_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="PetoraBD_{report_type}_report.csv"'
            writer = csv.writer(response)
            writer.writerow(columns)
            for row in data_rows: writer.writerow(row)
            return response

        # ---------------------------------------------------------
        # EXPORT LOGIC: PDF
        # ---------------------------------------------------------
        elif file_format == 'pdf':
            # Create dynamic HTML table for PDF
            table_headers = "".join([f"<th>{col}</th>" for col in columns])
            table_rows = "".join([
                "<tr>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>" 
                for row in data_rows
            ])
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    @page {{ size: A4; margin: 1.5cm; }}
                    body {{ font-family: Helvetica, sans-serif; color: #333; }}
                    .header {{ text-align: center; border-bottom: 2px solid #10b981; padding-bottom: 10px; margin-bottom: 20px; }}
                    .header h1 {{ color: #10b981; margin: 0; font-size: 24px; }}
                    .header p {{ color: #666; font-size: 12px; margin: 5px 0 0 0; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                    th {{ background-color: #f8fafc; color: #334155; font-weight: bold; padding: 10px; border: 1px solid #e2e8f0; text-align: left; font-size: 12px; }}
                    td {{ padding: 10px; border: 1px solid #e2e8f0; color: #475569; font-size: 11px; }}
                    .footer {{ margin-top: 30px; text-align: center; font-size: 10px; color: #94a3b8; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Petora BD</h1>
                    <p>{report_type.replace('_', ' ').title()} Analytics Report</p>
                    <p>Generated on: {now.strftime('%B %d, %Y')}</p>
                </div>
                <table>
                    <thead><tr>{table_headers}</tr></thead>
                    <tbody>{table_rows}</tbody>
                </table>
                <div class="footer">Confidential Business Document - Petora BD Admin Portal</div>
            </body>
            </html>
            """

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="PetoraBD_{report_type}_report.pdf"'
            
            # Convert HTML to PDF
            pisa_status = pisa.CreatePDF(html_content, dest=response)
            
            if pisa_status.err:
                return HttpResponse("Failed to generate PDF document.", status=500)
            
            return response

        return HttpResponse("The requested file format is not supported.", status=400)

    except Exception as e:
        print("--- REPORT EXPORT ERROR ---")
        traceback.print_exc()
        return HttpResponse("An unexpected error occurred while generating the report. Please try again.", status=500)