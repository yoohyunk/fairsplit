from django.db import models
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    username = models.CharField(max_length=150, unique=True)
    bio = models.TextField(blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.username