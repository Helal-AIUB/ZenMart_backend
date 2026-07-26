from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product, Collection
from tags.models import TaggedItem
from django.db.models import Value, Q, F, Func, Count, ExpressionWrapper, DecimalField
from django.db.models.functions import Concat
from store.models import Customer, OrderItem, Order
from django.db.models.aggregates import Max, Min, Avg
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, connection

# Create your views here.

# @transaction.atomic()

def say_hello(request):
    # try:
    #     product = Product.objects.get(pk=1)
    # except ObjectDoesNotExist:
    #     pass


    
    # queryset = Product.objects.filter(unit_price__gt=20)
    # queryset = Product.objects.filter(unit_price__range=(20,30))
    # queryset2 = Product.objects.filter(title__icontains='coffee')
    # customers = Customer.objects.filter(Q(membership='G') & Q(id__lt=10))
    # product5 = Product.objects.all()[:5]
    # return render(request, 'hello.html', { 'name':'Mohsin', 'products':list(queryset),'product2':list(queryset2), 'customers': customers, 'product5':product5})

     
    # queryset = Product.objects.values('id', 'title', 'collection__title')
    #task solved from Mosh tutorial
    # queryset = Product.objects.filter(orderitem__isnull=False).order_by('title').distinct()   # both query are given same output
    # query = OrderItem.objects.values('product__title').order_by('product__title').distinct()

    # queryset = Product.objects.only('id','title')

    # queryset = Product.objects.select_related('collection')
    # queryset = Product.objects.prefetch_related('promotions').select_related('collection').all()
    # task Last 5 customer order and item
    # orders = Order.objects.select_related('customer').prefetch_related('items').order_by('-placed_at')[:5]        # last 5 orders task

    # return render(request, 'hello.html', { 'name':'Mohsin', 'orders': list(orders), 'product':list(queryset) })

    # #-----------------------Aggregate------------------
    # result = Product.objects.filter(collection__id = 1).aggregate(count = Count('id'), min_price = Min('unit_price'))

    # return render(request, 'hello.html', { 'name':'Mohsin', 'result': result })

    #-----------------------Annotate Object------------------
    # queryset = Customer.objects.annotate(is_new = Value(True))
    # queryset2 = Customer.objects.annotate(new_id = F('id')+1)

    #-----------------------Calling Database Function------------------
    # queryset = Customer.objects.annotate(
    #     #Concate
    #     full_name = Func(F('first_name'), Value(' '), F('last_name'), function = 'CONCAT')
    # )
    # queryset = Customer.objects.annotate(
    #     #Concate
    #     full_name = Concat('first_name', Value(' '), 'last_name')
    # )

    #-----------------------Grouping Data------------------
    # queryset = Customer.objects.annotate(
    #     order_count = Count('order') +1
    # )

    #-----------------------Expression Wrapper------------------
    # discounted_price = ExpressionWrapper(F('unit_price') * 0.8, output_field = DecimalField())
    # queryset = Product.objects.annotate(
    #     discounted_price = discounted_price
    # )

    # -----------------Generic relationship------------------------
    # TaggedItem.objects.get_tags_for(Product,1)


    # -----------------Queryset Cache------------------------
    # queryset = Product.objects.all()
    # queryset[0]
    # list(queryset)


    # -------------------------Creating Objects-------------
    # collection = Collection()
    # collection.title = 'video games'
    # collection.featured_product = Product(pk=1)
    # collection.save()

    # Collection.objects.Create(title='a', featured_product_id=1)    # another way to create objects


     # -------------------------Updating Objects-------------
    # collection = Collection.objects.get(pk=11)
    # collection.title = 'Games'
    # collection.featured_product = None
    # collection.save()

    # Collection.objects.filter(pk=11).update(featured_product= None)    # another way to update objects


    # -------------------------Deleting an Objects-------------
    # collection = Collection(pk=11)
    # collection.delete()

    # Collection.objects.filter(id__gt=5).delete()         # another way to delete objects


    #------------------------Transactions---------------------------------
    # with transaction.atomic():
    #     order = Order()
    #     order.customer_id = 1
    #     order.save()
    
    #     item = OrderItem()
    #     item.order = order
    #     item.product_id = 1
    #     item.quantity = 1
    #     item.unit_price = 10
    #     item.save()



    # ----------------------Executing Raw SQL Queries--------------------

    queryset = Product.objects.raw('SELECT * FROM store_product')
    
    # cursor = connection.cursor()
    # cursor.execute('')
    # cursor.close()

    return render(request, 'hello.html', { 'name':'Mohsin', 'result': list(queryset) })
