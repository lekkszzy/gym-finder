from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from .models import Gym, Area, Route, Facility
from .serializers import GymSerializer, AreaSerializer, RouteSerializer, FacilitySerializer
from .permissions import IsOwnerOrReadOnly, ReadOnly


class GymListCreateView(generics.ListCreateAPIView):
    """
    List all gyms or create a new gym.
    """
    queryset = Gym.objects.all()
    serializer_class = GymSerializer
    permission_classes = [IsAdminUser | ReadOnly]
    search_fields = ['name', 'address', 'facilities__name']
    ordering_fields = ['name', 'monthly_price']
    ordering = ['name']


class GymDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a gym instance
    """
    queryset = Gym.objects.all()
    serializer_class = GymSerializer
    permission_classes = [IsAdminUser | ReadOnly]


class AreaListCreateView(generics.ListCreateAPIView):
    """
    List all areas or create a new area.
    """
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAdminUser | ReadOnly]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class AreaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an area instance
    """
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAdminUser | ReadOnly]


class FacilityListCreateView(generics.ListCreateAPIView):
    """
    List all facilities or create a new facility.
    """
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = [IsAdminUser | ReadOnly]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class FacilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a facility instance
    """
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = [IsAdminUser | ReadOnly]


class RouteListCreateView(generics.ListCreateAPIView):
    """
    List all routes or create a new route.
    """
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    def perform_create(self, serializer):
        # code is from https://www.django-rest-framework.org/api-guide/generic-views/#save-and-deletion-hooks
        serializer.save(owner=self.request.user)


class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a route instance
    """
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]