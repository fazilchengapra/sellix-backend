from django.urls import path
from .views import TicketView, TicketCloseView, TicketDetailedView, TicketReOpen, TicketAttachmentView

urlpatterns = [
    path('', TicketView.as_view()),
    path('<int:ticket_id>/', TicketDetailedView.as_view()),
    path('<int:ticket_id>/close/', TicketCloseView.as_view()),
    path('<int:ticket_id>/re-open/', TicketReOpen.as_view()),
    path('<int:ticket_id>/attachment/', TicketAttachmentView.as_view())
]