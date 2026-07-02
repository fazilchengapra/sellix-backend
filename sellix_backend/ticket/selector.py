from .models import Ticket, Order


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
        print('yeeeeeessss!')
        return False
    except Order.MultipleObjectsReturned:
        return False
