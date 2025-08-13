from django.db import models
from apps.users.models import User

# Create your models here.


class Split(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='splits/', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='splits')
    
    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    value = models.DecimalField(max_digits=10, decimal_places=2)
    split = models.ForeignKey(Split, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return self.name