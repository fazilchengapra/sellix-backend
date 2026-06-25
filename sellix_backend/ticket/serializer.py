from rest_framework import serializers
from .models import Ticket, TicketMessage, TicketAttachment

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['id', 'order', 'category', 'subject', 'status', 'priority', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

class TicketAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAttachment
        fields = ['file_url', 'cloudinary_public_id']

class TicketMessageSerializer(serializers.ModelSerializer):
    attachments = TicketAttachmentSerializer(many=True, required=False)
    class Meta:
        model = TicketMessage
        fields = ['id','message','attachments', 'is_staff_reply']

    def create(self, validated_data):
        attachments = validated_data.pop('attachments', [])
        message = TicketMessage.objects.create(**validated_data)

        TicketAttachment.objects.bulk_create([TicketAttachment(message=message ,**attachment) for attachment in attachments])

        return message

class TicketDetailedViewSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True)
    class Meta:
        model = Ticket
        fields = '__all__'