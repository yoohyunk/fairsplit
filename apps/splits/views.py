from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from splits.models import Split, Item
from .serializers import SplitSerializer, ItemSerializer
from rest_framework import viewsets

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

class ItemViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Item instances.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
