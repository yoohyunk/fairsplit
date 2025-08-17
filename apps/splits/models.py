from django.db import models
from apps.users.models import User

# Create your models here.


class Split(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('finalized', 'Finalized'),
        ('cancelled', 'Cancelled')
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='splits/', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='splits')
    
    # New fields for receipt integration
    receipt = models.ForeignKey('scan.ReceiptImage', on_delete=models.SET_NULL, null=True, blank=True, related_name='splits')
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    finalization_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.name


class SplitParticipant(models.Model):
    """
    스플릿에 참여하는 사람들을 관리하는 모델
    """
    split = models.ForeignKey(Split, on_delete=models.CASCADE, related_name='participants')
    email = models.EmailField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='split_participations')
    joined_at = models.DateTimeField(auto_now_add=True)
    agreed = models.BooleanField(default=False)
    agreed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['split', 'email']
    
    def __str__(self):
        return f"{self.email} in {self.split.name}"


class ItemAssignment(models.Model):
    """
    스플릿의 아이템들을 참여자들에게 할당하는 모델
    """
    split = models.ForeignKey(Split, on_delete=models.CASCADE, related_name='assignments')
    receipt_item = models.ForeignKey('scan.ReceiptItem', on_delete=models.CASCADE, related_name='assignments')
    participants = models.ManyToManyField(SplitParticipant, related_name='assigned_items')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['split', 'receipt_item']
    
    def __str__(self):
        participant_names = ', '.join([p.email for p in self.participants.all()])
        return f"{self.receipt_item.name} -> {participant_names}"


class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    value = models.DecimalField(max_digits=10, decimal_places=2)
    split = models.ForeignKey(Split, on_delete=models.CASCADE, related_name='items')

    def __str__(self):
        return self.name