from rest_framework import serializers
from .models import Split, Item, SplitParticipant, ItemAssignment

class SplitParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitParticipant
        fields = ['id', 'email', 'user', 'joined_at', 'agreed', 'agreed_at']
        read_only_fields = ['id', 'joined_at']

class ItemAssignmentSerializer(serializers.ModelSerializer):
    participants = SplitParticipantSerializer(many=True, read_only=True)
    receipt_item_name = serializers.CharField(source='receipt_item.name', read_only=True)
    receipt_item_price = serializers.DecimalField(source='receipt_item.total_price_with_discount', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ItemAssignment
        fields = ['id', 'receipt_item', 'receipt_item_name', 'receipt_item_price', 'participants', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']

class ReceiptInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    store_name = serializers.CharField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)

class SplitListSerializer(serializers.ModelSerializer):
    """Ultra-lightweight serializer for list view"""
    receipt_info = serializers.SerializerMethodField()
    participant_count = serializers.IntegerField(read_only=True)  # From annotation
    
    class Meta:
        model = Split
        fields = ['id', 'name', 'description', 'date_created', 'receipt_info', 'currency', 'status', 'participant_count']
    
    def get_receipt_info(self, obj):
        # Use prefetched receipt data directly
        if hasattr(obj, 'receipt') and obj.receipt:
            return {
                'id': obj.receipt.id,
                'store_name': obj.receipt.store_name or 'Unknown Store',
                'total_price': str(obj.receipt.total),
                'subtotal': str(obj.receipt.subtotal)
            }
        return None

class SplitSerializer(serializers.ModelSerializer):
    participants = SplitParticipantSerializer(many=True, read_only=True)
    assignments = ItemAssignmentSerializer(many=True, read_only=True)
    receipt_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Split
        fields = ['id', 'name', 'description', 'date_created', 'receipt', 'receipt_info', 'currency', 'status', 'finalization_date', 'participants', 'assignments']
        read_only_fields = ['date_created', 'participants', 'assignments', 'finalization_date', 'receipt_info']
    
    def get_receipt_info(self, obj):
        if obj.receipt:
            return {
                'id': obj.receipt.id,
                'store_name': obj.receipt.store_name or 'Unknown Store',
                'total_price': str(obj.receipt.total),
                'subtotal': str(obj.receipt.subtotal)
            }
        return None

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'value', 'split']
        read_only_fields = ['id']

