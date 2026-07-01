from django.urls import path
from .views import TicketView, TicketReplyView, TicketCloseView, TicketDetailedView, TicketReOpen

urlpatterns = [
    path('', TicketView.as_view()),
    path('<int:ticket_id>/', TicketDetailedView.as_view()),
    path('<int:ticket_id>/replay/', TicketReplyView.as_view()),
    path('<int:ticket_id>/close/', TicketCloseView.as_view()),
    path('<int:ticket_id>/re-open/', TicketReOpen.as_view())
]