from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import CarViewSet

router = SimpleRouter()
router.register('', CarViewSet, basename='cars')

urlpatterns = [
    path('', include(router.urls)),
]
