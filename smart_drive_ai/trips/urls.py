from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import RegisterAPIView, TripAPIView


router = DefaultRouter()


urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterAPIView.as_view()),
    path('auth/login/', TokenObtainPairView.as_view()),
    path('upload/', TripAPIView.as_view())
]
