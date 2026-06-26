from django.urls import path
from .views import TicketListView, TicketMessageView, TicketResolveView

urlpatterns = [
    path('<int:ticket_id>/reply/', TicketMessageView.as_view()),
    path('<int:ticket_id>/resolve/', TicketResolveView.as_view()),
    path('', TicketListView.as_view())
]
