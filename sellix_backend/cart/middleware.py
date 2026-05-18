import uuid
from django.utils.deprecation import MiddlewareMixin

class GuestCartMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if not request.user or request.user.is_anonymous:
            guest_id = request.COOKIES.get('guest_id')

            if not guest_id:
                new_guest_id = str(uuid.uuid4())

                response.set_cookie(
                    'guest_id',
                    new_guest_id,
                    max_age=7 * 24 * 60 * 60,  
                    httponly=True,             
                    samesite='Lax',            
                    secure=True
                )
        return response
        