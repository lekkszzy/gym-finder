from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.map_view, name='map'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    # PWA: service worker must live at the site root to control every page
    path('sw.js', views.service_worker, name='service-worker'),
    path('offline/', views.offline_view, name='offline'),
]