from django.urls import path
from .views import DashboardSummaryView, RevenueTrendView, StationUsageView, ShiftActivityView

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('revenue-trend/', RevenueTrendView.as_view(), name='dashboard-revenue-trend'),
    path('station-usage/', StationUsageView.as_view(), name='dashboard-station-usage'),
    path('shift-activity/', ShiftActivityView.as_view(), name='dashboard-shift-activity'),
]
