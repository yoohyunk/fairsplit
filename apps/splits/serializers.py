from rest_framework import serializers
from .models import Split, Item, SplitParticipant

class SplitParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitParticipant
        fields = ['id', 'email', 'user', 'joined_at', 'agreed', 'agreed_at']
        read_only_fields = ['id', 'joined_at']

class SplitSerializer(serializers.ModelSerializer):
    participants = SplitParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Split
        fields = ['id', 'name', 'description', 'date_created', 'receipt', 'currency', 'status', 'participants']
        read_only_fields = ['date_created', 'participants']

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'value', 'split']
        read_only_fields = ['id']

