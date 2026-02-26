from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Auth ──────────────────────────────────────────────
    path('api/auth/', include('users.urls.auth_urls')),

    # ── Admin ─────────────────────────────────────────────
    path('api/admin/', include('users.urls.admin_urls')),

    # ── Stations ──────────────────────────────────────────
    path('api/stations/', include('stations.urls')),

    # ── Chargers + Shifts ─────────────────────────────────
    path('api/chargers/', include('chargers.urls')),

    # ── Charging Sessions ─────────────────────────────────
   path('api/sessions/', include('charging_sessions.urls')),
]