from rest_framework.serializers import ModelSerializer
from .models import CustomUser
from rest_framework import serializers


class CustomUserSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True, required=False)

    def validate(self, data):
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if not password:
            raise serializers.ValidationError("Password is required")

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")

        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)  # 🔥 remove it

        password = validated_data.pop("password")

        user = CustomUser(**validated_data)
        user.set_password(password)  # 🔐 hash password
        user.save()

        return user

    class Meta:
        model = CustomUser
        fields = ["id", "email", "password", "confirm_password", "name"]
