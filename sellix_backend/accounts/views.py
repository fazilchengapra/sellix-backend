from users.models import CustomUser
from users.serializer import CustomUserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import PasswordResetToken
from .serializers import (
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
)
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from users.models import CustomUser as User
from .serializers import VerifyAccountSerializer
from rest_framework.permissions import AllowAny
from .models import EmailVerificationToken
from .utils import send_verification_email
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from drf_spectacular.utils import extend_schema

import uuid

#utils
from .utils import mergeCart


# Create your views here.
class RegisterViewSet(APIView):
    
    @extend_schema(
        request=CustomUserSerializer,
        responses=CustomUserSerializer,
        tags=["User"],
    )
    def post(self, req):
        serializer = CustomUserSerializer(data=req.data)
        if serializer.is_valid():
            user = serializer.save()
            verification_token = EmailVerificationToken.objects.create(user=user)
            send_verification_email(user, verification_token)
            return Response(
                    {
                        "message": "User registered successfully. Please check your email to verify your account.",
                        "token_for_testing": str(verification_token.token),
                    },
                    status=201,
                )
        return Response(serializer.errors, status=400)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=None,
        responses=None,
        tags=["User"],
    )
    def post(self, request):
        # Blacklist the refresh token
        refresh_token = request.COOKIES.get('refresh_token')
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as err:
                print(err)
                return Response({'message':"something went wrong."}, status=status.HTTP_400_BAD_REQUEST)
            
            response = Response({
                "message":"logout success!"
            }, status=status.HTTP_200_OK)

            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")

            new_guest_id = uuid.uuid4()
            response.set_cookie(
                'guest_id',
                new_guest_id,
                max_age=7 * 24 * 60 * 60,  
                httponly=True,             
                samesite='None',            
                secure=True
            )

            return response



# take email and perform operation
class ForgotPasswordView(APIView):
    @extend_schema(
        request=ForgotPasswordSerializer,
        responses=None,
        tags=["User"],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)

            # Invalidate old tokens for this user
            PasswordResetToken.objects.filter(user=user, is_used=False).update(
                is_used=True
            )

            # Create new token
            reset_token = PasswordResetToken.objects.create(user=user)

            # Build reset link with frontend url
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token.token}"

            send_mail(
                subject="Password Reset Request",
                message=f"Hi {user.username},\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link expires in 15 minutes.\n\nIf you did not request this, ignore this email.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )

            return Response(
                {
                    "message": "Password reset link sent to your email.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Step 2: User clicks link → validate token → set new password
class ResetPasswordView(APIView):
    @extend_schema(
        request=ResetPasswordSerializer,
        responses=None,
        tags=["User"],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data["token"]
            new_password = serializer.validated_data["new_password"]

            try:
                reset_token = PasswordResetToken.objects.get(token=token)
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
                )

            # Check if token is valid
            if not reset_token.is_valid():
                return Response(
                    {"error": "Token has expired or already been used."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Set new password
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            # Mark token as used
            reset_token.is_used = True
            reset_token.save()

            return Response(
                {"message": "Password reset successful. You can now log in."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Change Password (logged-in user only)
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses=None,
        tags=["User"],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data["old_password"]
            new_password = serializer.validated_data["new_password"]

            user = request.user

            # Check old password is correct
            if not user.check_password(old_password):
                return Response(
                    {"error": "Old password is incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Set new password
            user.set_password(new_password)
            user.save()

            return Response(
                {"message": "Password changed successfully."}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyAccountView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses=None,
        tags=["User"],
    )
    def post(self, request):
        serializer = VerifyAccountSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token_obj = serializer.context["token_obj"]
        user = token_obj.user

        # Mark user as verified
        user.is_verified = True  # or a custom field like user.is_verified = True
        user.save(update_fields=["is_verified"])

        # Mark token as used
        token_obj.is_used = True
        token_obj.save(update_fields=["is_used"])

        guest_id = request.COOKIES.get('guest_id')
        mergeCart(user, guest_id=guest_id,is_sign_up=True)

        response = Response(
            {"detail": "Account verified successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )

        response.delete_cookie('guest_id')
        return response

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        access = serializer.validated_data['access']
        refresh = serializer.validated_data['refresh']

        guest_id = request.COOKIES.get('guest_id')
        user = serializer.user

        if guest_id:
            mergeCart(user, guest_id)

        response = Response({"message":"Login success full for test"})


        response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=False,
            samesite='NOne',
            max_age=60*15
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=False,
            samesite='None',
            max_age=60*60*24*7
        )

        response.delete_cookie('guest_id')

        return response
    
class CookieTokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response({"error": "Refresh token missing"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            new_access = str(refresh.access_token)

            response = Response({"message": "Token refreshed"})
            response.set_cookie(
                key="access_token",
                value=new_access,
                httponly=True,
                secure=False,
                samesite="None",
                max_age=60 * 15 
            )
            return response

        except Exception:
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)
