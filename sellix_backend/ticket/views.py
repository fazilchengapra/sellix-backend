from rest_framework.views import APIView
from rest_framework.response import Response
from .serializer import TicketSerializer, TicketMessageSerializer, TicketDetailedViewSerializer
from rest_framework import status
from common.permissions import IsNormalUser
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import Ticket, TicketMessage
from orders.models import Order
from django.db.models import Prefetch


def is_ticket_exist(ticket_id, user):
        try:
            ticket = Ticket.objects.get(id=ticket_id, user=user)
            return ticket
        except Ticket.DoesNotExist:
            return False
        except Ticket.MultipleObjectsReturned:
            return False
        
def is_order_exist_and_valid(order_id, user):
    try:
        ticket = Order.objects.get(id=order_id, user=user)
        return ticket
    except Order.DoesNotExist:
        return False
    except Order.MultipleObjectsReturned:
        return False
        
category_choices = [
        'general',
        'refund',
        'technical',
        'payment',
        'order_issue'
    ]

order_id_needed_categories = [
        'refund',
        'payment',
        'order_issue'
    ]

# Create your views here.
class TicketView(APIView):
    permission_classes = [IsNormalUser]

    def post(self, request):
        serializer = TicketSerializer(data=request.data)

        data = request.data
        category = data.get('category', None)
        order_id  = data.get('order', None)

        if category and category not in category_choices:
            return Response({'message':'Invalid category type!'}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
                if category in order_id_needed_categories:
                    if not order_id:
                        return Response({'error':'No orderId provided'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    order = is_order_exist_and_valid(order_id, request.user)

                    if not order:
                        return Response({'error':'Invalid orderId'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    serializer.save(user=request.user, order=order)
                    return Response({'message':'Ticket raised success!'}, status=status.HTTP_200_OK)
                
                serializer.save(user=request.user)
                return Response({'message':'Ticket raised success!'}, status=status.HTTP_200_OK)
            
        return Response({'message':'validation error!', 'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        queryset = Ticket.objects.filter(user=request.user)
        serializer = TicketSerializer(queryset, many=True)

        return Response({'message':'tickets fetched success!', 'data':serializer.data}, status=status.HTTP_200_OK)
    
class TicketDetailedView(APIView):
    permission_classes = [IsNormalUser]

    def get(self, request, ticket_id):
        ticket_detailed = is_ticket_exist(ticket_id, request.user)

        if ticket_detailed:
            ticket_detailed = (
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
            .get(id=ticket_id, user=request.user)
        )
            serializer = TicketDetailedViewSerializer(ticket_detailed)
            return Response({'message':'tickets fetched success!', 'data':serializer.data}, status=status.HTTP_200_OK)
        return Response({'error':'ticket not found'}, status=status.HTTP_400_BAD_REQUEST)
    
class TicketReplyView(APIView):

    permission_classes = [IsNormalUser]


    def post(self, request, ticket_id):

        ticket = is_ticket_exist(ticket_id, request.user)
        serializer = TicketMessageSerializer(data=request.data)

        if ticket and ticket.status == 'open' and serializer.is_valid():
            serializer.save(sender=request.user, ticket=ticket)

            return Response({'message':'message sent success', 'data':serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'message':'Something went wrong!'}, status=status.HTTP_400_BAD_REQUEST)
    
class TicketCloseView(APIView):

    permission_classes = [IsNormalUser]

    def patch(self, request, ticket_id):

        ticket = is_ticket_exist(ticket_id, request.user)

        if ticket and ticket.status == 'closed':
            return Response({'message':'ticket is already closed!'}, status=status.HTTP_400_BAD_REQUEST)

        if ticket:
            ticket.status='closed'
            ticket.save(update_fields=['status'])
            serializer = TicketSerializer(ticket)
            return Response({'message':'ticket status updated success!', 'data':serializer.data}, status=status.HTTP_200_OK)
        
        return Response({'message':'ticket status updated fail!'}, status=status.HTTP_400_BAD_REQUEST)
    

class TicketReOpen(APIView):

    permission_classes = [IsNormalUser]

    def patch(self, request, ticket_id):

        ticket = is_ticket_exist(ticket_id, request.user)

        if ticket and ticket.status == 'open':
            return Response({'message':'ticket is already open!'}, status=status.HTTP_400_BAD_REQUEST)

        if ticket:
            ticket.status='open'
            ticket.save(update_fields=['status'])
            serializer = TicketSerializer(ticket)
            return Response({'message':'ticket status updated success!', 'data':serializer.data}, status=status.HTTP_200_OK)
        
        return Response({'message':'ticket status updated fail!'}, status=status.HTTP_400_BAD_REQUEST)