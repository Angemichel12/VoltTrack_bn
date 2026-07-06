from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── API Documentation ─────────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ── Auth ──────────────────────────────────────────────
    path('api/auth/', include('users.urls.auth_urls')),

    # ── Admin ─────────────────────────────────────────────
    path('api/admin/', include('users.urls.admin_urls')),

    # ── Cars (shared: staff + admin; unique_price is admin-only) ──
    path('api/cars/', include('cars.urls')),

    # ── Stations ──────────────────────────────────────────
    path('api/stations/', include('stations.urls')),

    # ── Chargers + Shifts ─────────────────────────────────
    path('api/chargers/', include('chargers.urls')),

    # ── Charging Sessions ─────────────────────────────────
   path('api/sessions/', include('charging_sessions.urls')),

    # ── Reports ────────────────────────────────────────────
    path('api/reports/', include('reports.urls')),
]