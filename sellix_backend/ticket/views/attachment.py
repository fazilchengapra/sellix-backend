from ..selector import is_ticket_exist
from .base import NormalUserAPIView
from rest_framework.response import Response
from rest_framework import status
from ..services.upload_service import upload_ticket_files

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