from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework import status
from .models import Product, Collection
from django.db.models import Count
from .serializers import ProductSerializer, CollectionSerializer

class ProductList(ListCreateAPIView):
    queryset = Product.objects.select_related('collection').all()       # Generic View
    serializer_class = ProductSerializer
    # def get_queryset(self):                        # Mixin
    #     return Product.objects.select_related('collection').all()

    # def get_serializer_class(self):
    #     return ProductSerializer

    def get_serializer_context(self):
        return {'request': self.request}


    # def get(self, request, format=None):                 # class based view 
    #     queryset = Product.objects.select_related('collection').all()
    #     collection_id = request.query_params.get('collection_id')
        
    #     if collection_id is not None:
    #         queryset = queryset.filter(collection_id=collection_id)
            
    #     serializer = ProductSerializer(queryset, many=True, context={'request': request})
    #     return Response(serializer.data)

    # def post(self, request, format=None):
    #     serializer = ProductSerializer(data=request.data, context={'request': request})
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)


# @api_view(['GET', 'POST'])                              # remove model view
# def product_list(request):
#     if request.method == 'GET':
#         queryset = Product.objects.select_related('collection').all()
#         collection_id = request.query_params.get('collection_id')
#         if collection_id is not None:
#             queryset = queryset.filter(collection_id=collection_id)
#         serializer = ProductSerializer(queryset, many=True, context = {'request': request})
#         return Response(serializer.data)
#     elif request.method == 'POST':
#         serializer = ProductSerializer(data = request.data, context={'request': request})
#         serializer.is_valid(raise_exception = True)
#         serializer.save()
#         return Response(serializer.data, status = status.HTTP_201_CREATED)


class ProductDetail(RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'id'

    # def get(self, request, id, format=None):                  # class based view
    #     product = get_object_or_404(Product, pk=id)
    #     serializer = ProductSerializer(product, context={'request': request})
    #     return Response(serializer.data)

    # def put(self, request, id, format=None):
    #     product = get_object_or_404(Product, pk=id)
    #     serializer = ProductSerializer(product, data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data)

    def delete(self, request, id, format=None):
        product = get_object_or_404(Product, pk=id)
        if product.orderitems.count() > 0:
            return Response(
                {'ERROR': 'Product can not be deleted because it is associated with an order item'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# @api_view(['GET', 'PUT', 'DELETE'])              # Model View
# def product_detail(request, id):
#     product = get_object_or_404(Product, pk=id)
#     if request.method == 'GET':
#         serializer = ProductSerializer(product, context={'request': request})
#         return Response(serializer.data)
#     elif request.method == 'PUT':
#         serializer = ProductSerializer(product, data = request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
#     elif request.method == 'DELETE':
#         if product.orderitems.count() > 0:
#             return Response({'ERROR':'Product can not be deleted because it is associated with an order item'},status = status.HTTP_405_METHOD_NOT_ALLOWED)
#         product.delete()
#         return Response(status = status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
def collection_list(request):
    if request.method == 'GET':
        queryset = Collection.objects.annotate(products_count=Count('product')).all()
        serializer = CollectionSerializer(queryset, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = CollectionSerializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)


# @api_view(['GET'])
# def collection_list(request):
#     queryset = Collection.objects.all()
#     serializer = CollectionSerializer(queryset, many=True)
#     return Response(serializer.data)

@api_view()
def collection_detail(request, pk):
    collection = get_object_or_404(
        Collection.objects.annotate(products_count=Count('product')), 
        pk=pk
    )
    serializer = CollectionSerializer(collection)
    return Response(serializer.data)


    # try:
    #     product = Product.objects.get(pk=id)
    #     serializer = ProductSerializer(product)
    #     return Response(serializer.data)
    # except Product.DoesNotExist:
    #     return Response(status=status.HTTP_404_NOT_FOUND)
