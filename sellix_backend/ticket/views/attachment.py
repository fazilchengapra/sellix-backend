from ..selector import is_ticket_exist
from .base import AllowedAnyUserAPIView
from rest_framework.response import Response
from rest_framework import status
from ..services.upload_service import upload_ticket_files

class TicketAttachmentView(AllowedAnyUserAPIView):
    def post(self, request, ticket_id):

        user = request.user
        if not user.is_authenticated:
            user = {"guest_id": request.COOKIES.get("guest_id")}
        ticket = is_ticket_exist(ticket_id, user)
        print("ticket is", ticket)
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