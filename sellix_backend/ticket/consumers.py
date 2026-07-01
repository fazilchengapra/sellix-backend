import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Ticket, TicketMessage


class TicketConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.ticket_id = self.scope["url_route"]["kwargs"]["ticket_id"]
        self.room_group_name = f"ticket_{self.ticket_id}"

        user = self.scope["user"]
        print(f"user : {user}")

        # Only authenticated users
        if user.is_anonymous:
            await self.close()
            return

        # Verify the ticket belongs to this user (or is admin)
        ticket = await self.get_ticket(self.ticket_id, user)
        if not ticket:
            await self.close()
            return

        # Join the ticket's channel group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_body = data.get("message", "").strip()

        if not message_body:
            return

        user = self.scope["user"]
        saved = await self.save_message(self.ticket_id, user, message_body)

        # Broadcast to everyone in the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "ticket.message",   # maps to ticket_message() below
                "message_id": str(saved["id"]),
                "message": saved["message"],
                "sender_id": saved["sender_id"],
                "sender_name": saved["sender_name"],
                "is_staff_reply": saved["is_staff_reply"],
                "created_at": saved["created_at"],
            },
        )

    # Handler — called when group_send fires type "ticket.message"
    async def ticket_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "ticket.message",
            "message_id": event["message_id"],
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender_name": event["sender_name"],
            "is_staff_reply": event["is_staff_reply"],
            "created_at": event["created_at"],
        }))

    # ── DB helpers ──────────────────────────────────────────────

    @database_sync_to_async
    def get_ticket(self, ticket_id, user):
        try:
            qs = Ticket.objects.only("id", "user", "status")
            if user.is_staff:
                return qs.get(id=ticket_id)
            return qs.get(id=ticket_id, user=user)
        except Ticket.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, ticket_id, user, body):
        msg = TicketMessage.objects.create(
            ticket_id=ticket_id,
            sender=user,
            message=body,
            is_staff_reply =user.is_staff,
        )
        return {
            "id": msg.id,
            "message": msg.message,
            "sender_id": user.id,
            "sender_name": user.get_full_name() or user.email,
            "is_staff_reply": msg.is_staff_reply,
            "created_at": msg.created_at.isoformat(),
        }