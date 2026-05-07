from django.shortcuts import render
from rest_framework.views import APIView
from .models import CustomUser
from .serializer import CustomUserSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Create your views here.
class UserMeViewSet(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)
    
    def patch(self, req):
        
        if "password" in req.data:
            return Response({"error": "Password cannot be updatable from here"}, status=400)
        
        user = req.user
        serializer = CustomUserSerializer(user,data=req.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            print(serializer.data)
            return Response(serializer.data)
        return Response(serializer.errors, status=400)