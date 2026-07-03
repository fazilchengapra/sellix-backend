import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .services.ticket_ws_service import (
    create_ticket_message,
    get_ticket_for_participant,
)

logger = logging.getLogger(__name__)

TICKET_MESSAGE_EVENT = "ticket.message"

# Wrapped once at import time instead of re-wrapping on every
# connect()/receive() call.
_get_ticket_for_participant = database_sync_to_async(get_ticket_for_participant)
_create_ticket_message = database_sync_to_async(create_ticket_message)


class TicketConsumer(AsyncWebsocketConsumer):
    """
    Real-time messaging for a single support ticket.

    REST (see ticket/views/) owns ticket creation, history, close/reopen.
    This consumer only relays new messages to everyone subscribed to the
    ticket's room group (`ticket_<ticket_id>`).
    """

    async def connect(self):
        print("Connecting to ticket consumer")
        self.ticket_id = self.scope["url_route"]["kwargs"]["ticket_id"]
        self.room_group_name = f"ticket_{self.ticket_id}"
        user = self.scope["user"]

        if user.is_anonymous:
            print("Anonymous user detected, checking for guest_id in cookies")
            ticket = await _get_ticket_for_participant(
                self.ticket_id, {"guest_id": self.scope["cookies"].get("guest_id")}
            )
        else:
            ticket = await _get_ticket_for_participant(self.ticket_id, user)

        if not ticket:
            logger.debug(
                "WS reject: no access (user=%s, ticket=%s)", user.id, self.ticket_id
            )
            await self.close()
            return
        print("Ticket access granted, adding to group")

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "detail": "Invalid JSON payload.",
                    }
                )
            )
            return

        message_body = (data.get("message") or "").strip()
        attachments = data.get("attachments") or []

        if not message_body:
            return

        user = self.scope["user"]
        if user.is_anonymous:
            user = {"guest_id": self.scope["cookies"].get("guest_id")}
        saved = await _create_ticket_message(
            self.ticket_id, user, message_body, attachments
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": TICKET_MESSAGE_EVENT,  # -> ticket_message() handler below
                "message_id": str(saved["id"]),
                "message": saved["message"],
                "attachments": saved["attachments"],
                "sender_id": saved["sender_id"],
                "sender_name": saved["sender_name"],
                "is_staff_reply": saved["is_staff_reply"],
                "created_at": saved["created_at"],
            },
        )

    # Handler — called when group_send fires type "ticket.message"
    async def ticket_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": TICKET_MESSAGE_EVENT,
                    "message_id": event["message_id"],
                    "message": event["message"],
                    "attachments": event["attachments"],
                    "sender_id": event["sender_id"],
                    "sender_name": event["sender_name"],
                    "is_staff_reply": event["is_staff_reply"],
                    "created_at": event["created_at"],
                }
            )
        )
