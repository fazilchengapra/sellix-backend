from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializer import TicketViewSerializer, TicketMessageSerializer
from ticket.models import Ticket, TicketMessage
from common.permissions import IsAdminUser
from ticket.serializer import TicketDetailedViewSerializer
from django.db.models import Prefetch

def is_ticket_is_valid(ticket_id):
    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return None
    else:
        return ticket
    
class AdminAPIView(APIView):
    permission_classes = [IsAdminUser]

class TicketListView(AdminAPIView):
    
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
    
class TicketMessageView(AdminAPIView):

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
    
class TicketResolveView(AdminAPIView):

    def patch(self, request, ticket_id):

        ticket = is_ticket_is_valid(ticket_id)

        if not ticket:
            return Response({'error':'ticket is not valid'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status='resolved'
        ticket.save(update_fields=['status'])
        
        serializer = TicketViewSerializer(ticket)
        return Response({'message':'token status updated!', 'data':serializer.data}, status=status.HTTP_200_OK)
    
class TicketDetailedView(AdminAPIView):

    def get(self, request, ticket_id):

        ticket = is_ticket_is_valid(ticket_id)

        if not ticket:
            return Response({'error':'No ticket found'}, status=status.HTTP_404_NOT_FOUND)
        ticket = (
            Ticket.objects
            .select_related('order', 'user', 'assigned_to')   # FK forward joins
            .prefetch_related(
                Prefetch(
                    'messages',
                    queryset=TicketMessage.objects
                        .select_related('sender')              # FK forward inside prefetch
                        .prefetch_related('attachments')       # reverse FK from message
                        .order_by('created_at')
                )
            )
            .get(id=ticket_id)
        )
        serializer = TicketDetailedViewSerializer(ticket)

        return Response({'message':'Ticket fetched success!', 'data':serializer.data}, status=status.HTTP_200_OK)