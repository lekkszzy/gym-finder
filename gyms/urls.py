from django.urls import path
from . import views

app_name = 'gyms'

urlpatterns = [
    # Gyms
    path('gyms/', views.GymListCreateView.as_view(), name='gym-list'),
    path('gyms/<int:pk>/', views.GymDetailView.as_view(), name='gym-detail'),

    # Areas
    path('areas/', views.AreaListCreateView.as_view(), name='area-list'),
    path('areas/<int:pk>/', views.AreaDetailView.as_view(), name='area-detail'),

    # Routes
    path('routes/', views.RouteListCreateView.as_view(), name='route-list'),
    path('routes/<int:pk>/', views.RouteDetailView.as_view(), name='route-detail'),

    # Facilities
    path('facilities/', views.FacilityListCreateView.as_view(), name='facility-list'),
    path('facilities/<int:pk>/', views.FacilityDetailView.as_view(), name='facility-detail'),

    # Spatial queries (added next)
]