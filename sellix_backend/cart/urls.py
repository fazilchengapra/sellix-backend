from django.urls import path
from .views import CartView, CartDetailsView

urlpatterns = [
    path('<int:pk>/', CartDetailsView.as_view()),
    path('', CartView.as_view()),
]