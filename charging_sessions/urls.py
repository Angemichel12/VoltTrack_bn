from django.urls import path
from .views import RegisterCarView, SearchCarView, StartSessionView, EndSessionView, MySessionsView

urlpatterns = [
    path('register-car/',  RegisterCarView.as_view(),  name='register-car'),
    path('search-car/',    SearchCarView.as_view(),    name='search-car'),
    path('start/',         StartSessionView.as_view(), name='start-session'),
    path('end/',           EndSessionView.as_view(),   name='end-session'),
    path('my-sessions/',   MySessionsView.as_view(),   name='my-sessions'),
]