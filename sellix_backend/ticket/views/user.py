from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializer import (
    TicketSerializer,
    TicketMessageSerializer,
    TicketDetailedViewSerializer,
)
from rest_framework import status
from ..models import Ticket
from ..selector import is_ticket_exist, get_ticket_detailed
from ..services.ticket_service import create_ticket
from .base import NormalUserAPIView


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

        ticket_detailed = get_ticket_detailed(ticket_id, request.user)

        if not ticket_detailed:
            return Response(
                {"error": "ticket not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TicketDetailedViewSerializer(ticket_detailed)
        return Response(
            {"message": "tickets fetched success!", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def post(self, request, ticket_id):

        ticket = is_ticket_exist(ticket_id, request.user)

        if not ticket:
            return Response(
                {"error": "ticket not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if ticket.status != "open":
            return Response(
                {"error": "ticket is closed, cannot send message"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TicketMessageSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(sender=request.user, ticket=ticket)

        return Response(
            {"message": "Message sent success", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class TicketCloseView(NormalUserAPIView):

    def patch(self, request, ticket_id):

        ticket = is_ticket_exist(ticket_id, request.user)

        if not ticket:
            return Response(
                {"message": "Ticket not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if ticket.status == "closed":
            return Response(
                {"message": "ticket is already closed!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket.status = "closed"
        ticket.save(update_fields=["status"])
        serializer = TicketSerializer(ticket)
        return Response(
            {"message": "ticket status updated success!", "data": serializer.data},
            status=status.HTTP_200_OK,
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