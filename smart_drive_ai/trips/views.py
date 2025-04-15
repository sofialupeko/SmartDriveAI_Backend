from rest_framework import permissions
from rest_framework.generics import CreateAPIView

from .serializers import RegisterSerializer


class RegisterAPIView(CreateAPIView):
    """Регистрация нового пользователя."""

    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
