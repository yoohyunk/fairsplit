from django.db import models

# Create your models here.


class Split(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    value = models.DecimalField(max_digits=10, decimal_places=2)
    split = models.ForeignKey(Split, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return self.name