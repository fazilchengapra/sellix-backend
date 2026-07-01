from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        token = AccessToken(token_key)
        user_id = token["user_id"]
        return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist):
        return AnonymousUser()


class JWTCookieMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):

        # Extract headers
        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode()

        # Parse cookies into a dict
        cookies = {}
        for chunk in cookie_header.split(";"):
            if "=" in chunk:
                key, val = chunk.strip().split("=", 1)
                cookies[key.strip()] = val.strip()

        # Get the access token — match your cookie name exactly
        token = cookies.get("access_token")

        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)