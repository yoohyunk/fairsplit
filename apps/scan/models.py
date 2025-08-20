from django.db import models
from django.contrib.auth import get_user_model
from apps.splits.models import Split
from decimal import Decimal
from .utils import parse_receipt_text
import os
from django.utils import timezone

User = get_user_model()

# Create your models here.

class ReceiptImage(models.Model):
    image = models.URLField(max_length=1000)  # Store only image URL
    store_name = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, default='unknown')
    receipt_type = models.CharField(max_length=255, default='unknown')
    address = models.CharField(max_length=1000, blank=True)
    datetime = models.DateTimeField(default=timezone.now)
    currency = models.CharField(max_length=10, default='USD')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Store sub_total_amount
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Store total_price
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    all_items_price_with_tax = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=255, default='unknown')
    rounding = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxes_not_included_sum = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tips = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.store_name} - {self.datetime}"

    def save(self, *args, **kwargs):
        if not self.datetime:
            self.datetime = timezone.now()
        super().save(*args, **kwargs)
    
class ReceiptItem(models.Model):
    receipt = models.ForeignKey(ReceiptImage, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=1000)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    measurement_unit = models.CharField(max_length=50, default='ks')
    total_price_without_discount = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price_with_discount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category = models.CharField(max_length=255, default='Other')
    item_price_with_tax = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.total_price_with_discount}"

class TaxItem(models.Model):
    receipt = models.ForeignKey(ReceiptImage, on_delete=models.CASCADE, related_name='tax_items')
    tax_name = models.CharField(max_length=255)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    tax_from_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    tax_included = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tax_name} - {self.percentage}%"

