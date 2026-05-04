from django.shortcuts import render
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterViewSet

urlpatterns = [
    path("refresh/token/", TokenRefreshView.as_view()),
    path("login/", TokenObtainPairView.as_view()),
    path("register/", RegisterViewSet.as_view()),
]
