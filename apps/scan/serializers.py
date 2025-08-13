from rest_framework import serializers
from .models import ReceiptImage, ReceiptItem, TaxItem

class ReceiptItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiptItem
        fields = [
            'id', 
            'name', 
            'quantity', 
            'measurement_unit',
            'total_price_without_discount',
            'unit_price',
            'total_price_with_discount',
            'discount',
            'category',
            'item_price_with_tax',
            'created_at'
        ]

class TaxItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxItem
        fields = [
            'id',
            'tax_name',
            'percentage',
            'tax_from_amount',
            'tax',
            'total',
            'tax_included',
            'created_at'
        ]

class ReceiptImageSerializer(serializers.ModelSerializer):
    items = ReceiptItemSerializer(many=True, read_only=True)
    tax_items = TaxItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReceiptImage
        fields = [
            'id', 
            'image', 
            'store_name',
            'country',
            'receipt_type',
            'address',
            'datetime',
            'currency',
            'subtotal',
            'tax', 
            'total', 
            'total_discount',
            'all_items_price_with_tax',
            'payment_method',
            'rounding',
            'taxes_not_included_sum',
            'tips',
            'items',
            'tax_items',
            'created_at'
        ] 