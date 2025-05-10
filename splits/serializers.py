from rest_framework import serializers
from .models import Split, Item

class SplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Split
        fields = ['id', 'name', 'description', 'date_created']
        read_only_fields = ['date_created']

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'value', 'split']
        read_only_fields = ['']

