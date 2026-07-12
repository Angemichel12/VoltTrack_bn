from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ExpenseViewSet

router = SimpleRouter()
router.register('', ExpenseViewSet, basename='expenses')

urlpatterns = [
    path('', include(router.urls)),
]
