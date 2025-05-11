from rest_framework import permissions, viewsets
from rest_framework.generics import CreateAPIView, RetrieveAPIView

from .models import Trip, UserDrivingProfile
from .serializers import (
    RegisterSerializer, TripListSerializer, TripRetrieveSerializer,
    TripUploadSerializer, UserDrivingProfileSerializer
)


class RegisterAPIView(CreateAPIView):
    """Регистрация нового пользователя."""

    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)


class TripUploadAPIView(CreateAPIView):
    """Загрузка телеметрических данных поездки."""

    serializer_class = TripUploadSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение списка поездок пользователя или получение анализа поездки."""

    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Trip.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TripRetrieveSerializer
        return TripListSerializer


class UserDrivingProfileAPIView(RetrieveAPIView):
    """Получение агрегированных показателей."""

    serializer_class = UserDrivingProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return UserDrivingProfile.objects.get(user=self.request.user)
