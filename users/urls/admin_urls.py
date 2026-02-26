from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.admin_views import AdminUserViewSet, AdminStationViewSet

router = DefaultRouter()
router.register('users', AdminUserViewSet, basename='admin-users')
router.register('stations', AdminStationViewSet, basename='admin-stations')

urlpatterns = [
    path('', include(router.urls)),
]