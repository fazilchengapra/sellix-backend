from rest_framework import serializers
from ticket.models import Ticket, TicketMessage

class TicketViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'

class TicketMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = ['message']

