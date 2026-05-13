from django.urls import path
from .views import (
    UserListCreateView,
    UserRetrieveUpdateDeleteView,
    BlockUnblockUserView,
)

urlpatterns = [
    path("", UserListCreateView.as_view(), name="user-list-create"),
    path("<int:pk>/", UserRetrieveUpdateDeleteView.as_view(), name="user-detail"),
    path(
        "<int:pk>/block-unblock/",
        BlockUnblockUserView.as_view(),
        name="user-block-unblock",
    ),
]
