from rest_framework.views import APIView
from common.permissions import IsNormalUser

class NormalUserAPIView(APIView):
    permission_classes = [IsNormalUser]