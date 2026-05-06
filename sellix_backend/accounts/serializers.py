from rest_framework import serializers
from users.models import CustomUser as User
from .models import EmailVerificationToken


# Forgot Password - accepts email
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email.")
        return value


# Reset Password - accepts token + new password
class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=4, write_only=True)
    confirm_password = serializers.CharField(min_length=4, write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data


# Change Password - for logged-in users
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=4, write_only=True)
    confirm_password = serializers.CharField(min_length=4, write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class VerifyAccountSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            token_obj = EmailVerificationToken.objects.select_related("user").get(
                token=value
            )
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")

        if token_obj.is_used:
            raise serializers.ValidationError("This token has already been used.")

        if not token_obj.is_valid():
            raise serializers.ValidationError(
                "Token has expired. Please request a new one."
            )

        self.context["token_obj"] = token_obj
        return value
