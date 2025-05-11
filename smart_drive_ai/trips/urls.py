from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (
    RegisterAPIView, TripViewSet, TripUploadAPIView, UserDrivingProfileAPIView
)


router = DefaultRouter()

router.register(r'trips', TripViewSet, basename='trips')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterAPIView.as_view()),
    path('auth/login/', TokenObtainPairView.as_view()),
    path('upload/', TripUploadAPIView.as_view()),
    path('profile/', UserDrivingProfileAPIView.as_view())
]
