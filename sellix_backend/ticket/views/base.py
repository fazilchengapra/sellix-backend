from rest_framework.views import APIView
from common.permissions import IsNormalUser
from rest_framework.permissions import AllowAny

class NormalUserAPIView(APIView):
    permission_classes = [IsNormalUser]

class AllowedAnyUserAPIView(APIView):
    permission_classes = [AllowAny]