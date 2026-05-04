from users.models import CustomUser
from users.serializer import CustomUserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken


# Create your views here.
class RegisterViewSet(APIView):
    def post(self, req):
        serializer = CustomUserSerializer(data=req.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(CustomUserSerializer(user).data)
        return Response(serializer.errors, status=400)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Blacklist the refresh token
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=205)
        except Exception as e:
            return Response(status=400)
