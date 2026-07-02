from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializer import (
    TicketSerializer,
    TicketMessageSerializer,
    TicketDetailedViewSerializer,
)
from rest_framework import status
from common.permissions import IsNormalUser
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..models import Ticket, TicketMessage
from orders.models import Order
from django.db.models import Prefetch
import cloudinary.uploader
import uuid
from ..selector import is_ticket_exist
from ..services.upload_service import upload_ticket_files
from ..services.ticket_service import create_ticket


class NormalUserAPIView(APIView):
    permission_classes = [IsNormalUser]


# Create your views here.
class TicketView(NormalUserAPIView):

    def post(self, request):
        serializer = TicketSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        create_ticket(serializer, request.user)

        return Response(
            {"message": "Ticket raised success!"}, status=status.HTTP_200_OK
        )

    def get(self, request):
        queryset = Ticket.objects.filter(user=request.user)
        serializer = TicketSerializer(queryset, many=True)

        return Response(
            {"message": "tickets fetched success!", "data": serializer.data},
            status=status.HTTP_200_OK,
        )


class TicketDetailedView(NormalUserAPIView):

    def get(self, request, ticket_id):
        ticket_detailed = is_ticket_exist(ticket_id, request.user)

        if ticket_detailed:
            ticket_detailed = (
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
                .get(id=ticket_id, user=request.user)
            )
            serializer = TicketDetailedViewSerializer(ticket_detailed)
            return Response(
                {"message": "tickets fetched success!", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "ticket not found"}, status=status.HTTP_400_BAD_REQUEST
        )

    def post(self, request, ticket_id):

        ticket = is_ticket_exist(ticket_id, request.user)
        serializer = TicketMessageSerializer(data=request.data)

        if ticket and ticket.status == "open" and serializer.is_valid():
            serializer.save(sender=request.user, ticket=ticket)

            return Response(
                {"message": "message sent success", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"message": "Something went wrong!"}, status=status.HTTP_400_BAD_REQUEST
        )


class TicketCloseView(NormalUserAPIView):

    def patch(self, request, ticket_id):

        ticket = is_ticket_exist(ticket_id, request.user)

        if ticket and ticket.status == "closed":
            return Response(
                {"message": "ticket is already closed!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ticket:
            ticket.status = "closed"
            ticket.save(update_fields=["status"])
            serializer = TicketSerializer(ticket)
            return Response(
                {"message": "ticket status updated success!", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"message": "ticket status updated fail!"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TicketReOpen(NormalUserAPIView):

    def patch(self, request, ticket_id):

        ticket = is_ticket_exist(ticket_id, request.user)

        if ticket and ticket.status == "open":
            return Response(
                {"message": "ticket is already open!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ticket:
            ticket.status = "open"
            ticket.save(update_fields=["status"])
            serializer = TicketSerializer(ticket)
            return Response(
                {"message": "ticket status updated success!", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"message": "ticket status updated fail!"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TicketAttachmentView(NormalUserAPIView):
    def post(self, request, ticket_id):

        ticket = is_ticket_exist(ticket_id, request.user)

        if not ticket:
            return Response(
                {"message": "Ticket not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        files = request.FILES.getlist("attachments")

        try:
            attachments = upload_ticket_files(ticket_id, files)

        except Exception as e:
            print(e)
            return Response(
                {"error": "Image upload failed"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "image uploaded success", "data": attachments},
            status=status.HTTP_200_OK,
        )
