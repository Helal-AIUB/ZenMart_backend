from rest_framework import serializers
from decimal import Decimal
from store.models import Product, Collection

class CollectionSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Collection
        fields = ['id', 'title', 'products_count']
        read_only_fields = ['products_count']



class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product            # Model serializer
        fields = ['id', 'title', 'description', 'slug', 'inventory', 'unit_price', 'collection']

    # id = serializers.IntegerField()               # Serializing relationship
    # title = serializers.CharField(max_length = 255)
    # price = serializers.DecimalField(6, decimal_places=2, source='unit_price')
    # unit_price_with_tax = serializers.SerializerMethodField(method_name = 'calculate_tax')
    # collection = serializers.HyperlinkedRelatedField(
    #     queryset = Collection.objects.all(),
    #     view_name = 'collection-detail'
    # )

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)
    
    # def validate(self, data):
    #     if data['password'] != data['confirm_password']:
    #         return serializers.ValidationError("'Password do not match!")
    #     return data

    # def create(self, validated_data):
    #     product = Product(**validated_data)
    #     product.other = 1
    #     product.save()
    #     return product
    
    # def update(self, instance, validated_data):
    #     instance.unit_price = validated_data.get('unit_price')
    #     instance.save()
    #     return instance