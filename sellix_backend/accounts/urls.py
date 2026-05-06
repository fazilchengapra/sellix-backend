from django.shortcuts import render
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterViewSet, LogoutView
from .views import ForgotPasswordView, ResetPasswordView, ChangePasswordView, VerifyAccountView
from .views import CustomTokenObtainPairView

# Create your views here.

urlpatterns = [
    path("refresh/token/", TokenRefreshView.as_view()),
    path("login/", CustomTokenObtainPairView.as_view()),
    path("register/", RegisterViewSet.as_view()),
    path('logout/', LogoutView.as_view()),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("verify-account/", VerifyAccountView.as_view(), name="verify-account"),
]