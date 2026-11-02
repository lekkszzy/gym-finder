from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.map_view, name='map'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
]