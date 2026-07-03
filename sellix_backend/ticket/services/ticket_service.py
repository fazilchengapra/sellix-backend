from ..constants import ORDER_REQUIRED_CATEGORIES
from ..selector import is_order_exist
from rest_framework.exceptions import ValidationError

def create_ticket(serializer, user_selector):
    category = serializer.validated_data.get("category", None)
    order_id = serializer.validated_data.get("order", None)

    user = user_selector.get("user") if "user" in user_selector else None

    if category in ORDER_REQUIRED_CATEGORIES:
        if not order_id:
            raise ValidationError({"order":"Order is required"})
        
        if not user:
            raise ValidationError({"user":"Unauthenticated user cannot create ticket with order"})

        order = is_order_exist(order_id.id, user)

        if not order:
            raise ValidationError({"order":"Invalid order"})

        return serializer.save(user=user, order=order)

    return serializer.save(**user_selector)