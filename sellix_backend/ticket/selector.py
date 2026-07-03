from .models import Ticket, Order
from .models import TicketMessage
from django.db.models import Prefetch


def get_user_selector(request):
    if request.user.is_authenticated:
        return {"user": request.user}
    else:
        return {"guest_id": request.COOKIES.get("guest_id")}


def is_ticket_exist(ticket_id, user_selector):
    
    if isinstance(user_selector, dict):
        filter = user_selector
    else:
        filter = {'user':user_selector}

    try:
        ticket = Ticket.objects.get(
            id=ticket_id,
            **filter
        )
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


def get_ticket_detailed(ticket_id, user_selector):
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
        .filter(id=ticket_id, **user_selector)
        .first()
    )
