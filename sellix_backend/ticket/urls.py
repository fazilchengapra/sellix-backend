from django.urls import path
from .views import TicketView, TicketReplyView, TicketCloseView, TicketDetailedView

urlpatterns = [
    path('', TicketView.as_view()),
    path('<int:ticket_id>/', TicketDetailedView.as_view()),
    path('<int:ticket_id>/replay/', TicketReplyView.as_view()),
    path('<int:ticket_id>/close/', TicketCloseView.as_view()),
    path('<int:ticket_id>/re-open/', TicketCloseView.as_view())
]
