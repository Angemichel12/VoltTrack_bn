from django.urls import path
from .views import (
    ChargerListCreateView,
    OpenShiftView,
    CloseShiftView,
    ShiftHistoryView,
)

urlpatterns = [
    # ── Admin + Staff ─────────────────────────────────────
    path('', ChargerListCreateView.as_view(), name='charger-list-create'),

    # ── Shifts ────────────────────────────────────────────
    path('shifts/open/', OpenShiftView.as_view(), name='shift-open'),
    path('shifts/<int:pk>/close/', CloseShiftView.as_view(), name='shift-close'),
    path('shifts/history/', ShiftHistoryView.as_view(), name='shift-history'),
]