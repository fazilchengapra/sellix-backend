"""
Database-facing helpers for the ticket WebSocket consumer.

These are plain sync functions — no async/await, no database_sync_to_async
in here. That keeps them reusable from any sync context (REST views, shell,
management commands, tests) and leaves the async<->sync bridging to the
consumer, which is the only place that actually needs it.
"""

from django.db import transaction

from ..models import Ticket, TicketAttachment, TicketMessage


def get_ticket_for_participant(ticket_id, user):
    """
    Return the Ticket if `user` may access it (owner, or staff), else None.
    Used to gate WebSocket connect().
    """
    qs = Ticket.objects.only("id", "user", "status", "guest_id")
    if type(user) is dict and "guest_id" in user:
        try:
            return qs.get(guest_id=user["guest_id"], id=ticket_id)
        except Ticket.DoesNotExist:
            return None

    try:
        if user.is_staff:
            return qs.get(id=ticket_id)
        return qs.get(id=ticket_id, user=user)
    except Ticket.DoesNotExist:
        return None


def create_ticket_message(ticket_id, user, body, attachments):
    if type(user) is dict and "guest_id" in user:
        user = user["guest_id"]
    """
    Persist a ticket message and its attachments atomically, and return
    a plain dict shaped for the WS broadcast payload.

    Attachment items missing `file_url` / `cloudinary_public_id` are
    skipped rather than raising, since an uncaught KeyError inside an
    async consumer is harder to surface cleanly than in a normal view.
    """
    with transaction.atomic():
        msg = TicketMessage.objects.create(
            ticket_id=ticket_id,
            sender=user if type(user) is not str else None,
            message=body,
            is_staff_reply=user.is_staff if type(user) is not str else False,
        )

        valid_attachments = [
            item
            for item in attachments
            if "file_url" in item and "cloudinary_public_id" in item
        ]
        if valid_attachments:
            TicketAttachment.objects.bulk_create(
                [
                    TicketAttachment(
                        message=msg,
                        file_url=item["file_url"],
                        cloudinary_public_id=item["cloudinary_public_id"],
                    )
                    for item in valid_attachments
                ]
            )

    return {
        "id": msg.id,
        "message": msg.message,
        "attachments": attachments,
        "sender_id": user if type(user) is str else user.id,
        "sender_name": (
            user.get_full_name() or user.email if type(user) is not str else "Guest"
        ),
        "is_staff_reply": msg.is_staff_reply,
        "created_at": msg.created_at.isoformat(),
    }
