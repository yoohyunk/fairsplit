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

class SplitSerializer(serializers.ModelSerializer):
    participants = SplitParticipantSerializer(many=True, read_only=True)
    assignments = ItemAssignmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Split
        fields = ['id', 'name', 'description', 'date_created', 'receipt', 'currency', 'status', 'participants', 'assignments']
        read_only_fields = ['date_created', 'participants', 'assignments']

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'value', 'split']
        read_only_fields = ['id']

