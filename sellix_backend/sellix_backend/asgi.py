import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from sellix_backend.jwt_auth_middleware import JWTCookieMiddleware
import ticket.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sellix.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JWTCookieMiddleware(
            URLRouter(
                ticket.routing.websocket_urlpatterns
            )
        )
    ),
})