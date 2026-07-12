from django.urls import path
from .views import (
    SessionReportView, SessionReportExcelView, SessionReportPdfView,
    ShiftReportView, ShiftReportExcelView, ShiftReportPdfView,
    ExpenseReportView, ExpenseReportExcelView, ExpenseReportPdfView,
)

urlpatterns = [
    path('sessions/', SessionReportView.as_view(), name='report-sessions'),
    path('sessions/excel/', SessionReportExcelView.as_view(), name='report-sessions-excel'),
    path('sessions/pdf/', SessionReportPdfView.as_view(), name='report-sessions-pdf'),

    path('shifts/', ShiftReportView.as_view(), name='report-shifts'),
    path('shifts/excel/', ShiftReportExcelView.as_view(), name='report-shifts-excel'),
    path('shifts/pdf/', ShiftReportPdfView.as_view(), name='report-shifts-pdf'),

    path('expenses/', ExpenseReportView.as_view(), name='report-expenses'),
    path('expenses/excel/', ExpenseReportExcelView.as_view(), name='report-expenses-excel'),
    path('expenses/pdf/', ExpenseReportPdfView.as_view(), name='report-expenses-pdf'),
]
