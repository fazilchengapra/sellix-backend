import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sellix_backend.settings")
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from .jwt_auth_middleware import JWTCookieMiddleware
import ticket.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTCookieMiddleware(
            URLRouter(ticket.routing.websocket_urlpatterns)
        ),
    }
)
