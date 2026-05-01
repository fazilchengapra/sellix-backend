from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class CustomUser(AbstractUser):
    ROLE_CHOICES = (("customer", "Customer"), ("admin", "Admin"))

    username = None
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS=['name']
