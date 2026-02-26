from django.urls import path,include
from .auth_views import RegisterView, LoginView, TokenRefreshView
from rest_framework.routers import DefaultRouter
from .admin_views import AdminUserViewSet, AdminStationViewSet

router = DefaultRouter()
router.register('users', AdminUserViewSet, basename='admin-users')
router.register('stations', AdminStationViewSet, basename='admin-stations')
urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('', include(router.urls)),
]