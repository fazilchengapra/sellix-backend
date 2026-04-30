from django.db import models


# Create your models here.
class CustomUser(models.Model):
    ROLE_CHOICES = (("customer", "Customer"), ("admin", "Admin"))
    
    username = None
    name = models.CharField(max_length=150)
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)