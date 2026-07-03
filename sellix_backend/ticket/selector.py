from .models import Ticket, Order
from .models import TicketMessage
from django.db.models import Prefetch


def is_ticket_exist(ticket_id, user):
    try:
        ticket = Ticket.objects.get(id=ticket_id, user=user)
        return ticket
    except Ticket.DoesNotExist:
        return False
    except Ticket.MultipleObjectsReturned:
        return False


def is_order_exist(order_id, user):
    try:
        order = Order.objects.get(id=order_id, user=user)
        return order
    except Order.DoesNotExist:
        return False
    except Order.MultipleObjectsReturned:
        return False


def get_ticket_detailed(ticket_id, user):
    return (
        Ticket.objects.select_related(
            "order", "user", "assigned_to"
        )  # FK forward joins
        .prefetch_related(
            Prefetch(
                "messages",
                queryset=TicketMessage.objects.select_related(
                    "sender"
                )  # FK forward inside prefetch
                .prefetch_related("attachments")  # reverse FK from message
                .order_by("created_at"),
            )
        )
        .filter(id=ticket_id, user=user).first()
    )
