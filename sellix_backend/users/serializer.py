from rest_framework.serializers import ModelSerializer
from .models import CustomUser
from rest_framework import serializers


class CustomUserSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["id", "email", "password", "name"]