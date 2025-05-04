from rest_framework import permissions
from rest_framework.generics import CreateAPIView

from .serializers import RegisterSerializer, TripSerializer


class RegisterAPIView(CreateAPIView):
    """Регистрация нового пользователя."""

    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)


class TripAPIView(CreateAPIView):
    """Загрузка телеметрических данных поездки."""

    serializer_class = TripSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
