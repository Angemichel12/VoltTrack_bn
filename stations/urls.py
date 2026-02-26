from django.urls import path
from .views import (
    AdminStationListCreateView,
    AdminStationDetailView,
    AdminReportsView,
    SetPriceView,
    StaffDashboardView,
    StaffReportsView,
    StationChargersView,
)

urlpatterns = [
    # ── Admin ────────────────────────────────────────────
    path('', AdminStationListCreateView.as_view(), name='admin-station-list-create'),
    path('<int:pk>/', AdminStationDetailView.as_view(), name='admin-station-detail'),
    path('<int:pk>/set-price/', SetPriceView.as_view(), name='admin-set-price'),
    path('reports/', AdminReportsView.as_view(), name='admin-reports'),

    # ── Staff ─────────────────────────────────────────────
    path('dashboard/', StaffDashboardView.as_view(), name='staff-dashboard'),
    path('chargers/', StationChargersView.as_view(), name='staff-station-chargers'),
    path('my-reports/', StaffReportsView.as_view(), name='staff-reports'),
]