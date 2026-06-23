from django.db import models
from orders.models import Order
from users.models import CustomUser

# Create your models here.

class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Ticket(TimeStamped):

    CATEGORY_CHOICES = [
        ('general', 'General Inquiry'),
        ('order_issue', 'Order Issue'),
        ('refund', 'Refund Request'),
        ('technical', 'Technical Problem'),
        ('payment', 'Payment Issue'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]


    order_id = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tickets')
    subject = models.CharField(max_length=70)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'is_staff':True}, related_name='assigned_tickets')

class TicketMessages(TimeStamped):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='ticket_messages')
    message = models.TextField()
    is_staff_reply = models.BooleanField(default=False)

class TicketAttachment(TimeStamped):
        message = models.ForeignKey(TicketMessages, on_delete=models.CASCADE, related_name='attachment')
        file_url = models.URLField()