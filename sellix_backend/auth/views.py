from users.models import CustomUser
from users.serializer import CustomUserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# Create your views here.
class RegisterViewSet(APIView):
    def post(self, req):
        serializer = CustomUserSerializer(data=req.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(CustomUserSerializer(user).data)
        return Response(serializer.errors, status=400)
