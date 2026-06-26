from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializer import TicketViewSerializer, TicketMessageSerializer
from ticket.models import Ticket
from common.permissions import IsAdminUser

def is_ticket_is_valid(ticket_id):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return None
    else:
        return ticket
class TicketListView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        ticket_status = request.query_params.get("status", None)

        valid_statuses = [
            'open','in_progress','resolved','close'
        ]

        if ticket_status in valid_statuses:
            queryset = Ticket.objects.filter(status=status)
        else:
            queryset = Ticket.objects.all()
        serializer = TicketViewSerializer(queryset, many=True)
        return Response({'message':'ticket data fetched success', 'data':serializer.data}, status=status.HTTP_200_OK)
    
class TicketMessageView(APIView):

    def post(self, request, ticket_id):

        ticket = is_ticket_is_valid(ticket_id)

        if not ticket:
            return Response({'error':'ticket is not valid'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = TicketMessageSerializer(data=request.data)

        if serializer.is_valid():
            post_data = {
                'sender':request.user,
                'ticket':ticket,
                'is_staff_reply': True,
            }
            serializer.save(**post_data)

            return Response({'message':'message sent success!', 'data':serializer.data}, status=status.HTTP_200_OK)
        return Response({'message':'message sent failed!', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
class TicketResolveView(APIView):

    def patch(self, request, ticket_id):

        ticket = is_ticket_is_valid(ticket_id)

        if not ticket:
            return Response({'error':'ticket is not valid'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status='resolved'
        ticket.save(update_fields=['status'])
        
        serializer = TicketViewSerializer(ticket)
        return Response({'message':'token status updated!', 'data':serializer.data}, status=status.HTTP_200_OK)