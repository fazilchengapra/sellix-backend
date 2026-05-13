from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from .serializers import UserSerializer
from users.models import CustomUser as User


def get_user_or_return_err(pk):
    try:
        return User.objects.get(pk=pk, is_deleted=False)
    except User.DoesNotExist:
        raise NotFound(detail=f"User with id {pk} not found.")


class UserListCreateView(APIView):

    def get(self, request):
        users = User.objects.filter(is_deleted=False)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserRetrieveUpdateDeleteView(APIView):

    def get(self, request, pk):
        user = get_user_or_return_err(pk)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        user = get_user_or_return_err(pk)
        serializer = UserSerializer(user, data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(UserSerializer(serializer.save()).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        user = get_user_or_return_err(pk)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response(UserSerializer(serializer.save()).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        user = get_user_or_return_err(pk)
        user.is_deleted = True
        user.save()
        return Response({"message": f"User {pk} deleted."}, status=status.HTTP_200_OK)
    
class BlockUnblockUserView(APIView):
    def post(self, request, pk):
        user = get_user_or_return_err(pk)
        user.is_active = not user.is_active
        user.save()
        status_str = "unblocked" if user.is_active else "blocked"
        return Response({"message": f"User {pk} {status_str}."}, status=status.HTTP_200_OK)