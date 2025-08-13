from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from apps.splits.models import Split, Item
from apps.splits.serializers import SplitSerializer, ItemSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

# Create your views here.

def index(request):
    return HttpResponse("Hello, world!")

def hello(request):
    return HttpResponse("Hello, world! This is the hello view.")

class SplitViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Split instances.
    """
    queryset = Split.objects.all()
    serializer_class = SplitSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Split.objects.filter(user=self.request.user)

class ItemViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Item instances.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Item.objects.filter(split__user=self.request.user)
