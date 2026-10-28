from .serializers import GymSerializer, AreaSerializer, RouteSerializer, FacilitySerializer
from rest_framework import generics
from .models import Gym, Area, Route, Facility
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .permissions import IsOwnerOrReadOnly

class GymListCreateView(generics.ListCreateAPIView):
    """
    List all gyms or create a new gym.
    """
    queryset = Gym.objects.all()
    search_fields = ['name', 'address', 'facilities__name']
    ordering_fields = ['name', 'monthly_price']
    ordering = ['name']

    serializer_class = GymSerializer

  
class GymDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a gym instance
    """
    queryset = Gym.objects.all()
    serializer_class = GymSerializer

   
   
class AreaListCreateView(generics.ListCreateAPIView):
    """
    List all areas or create a new area.
    """
    queryset = Area.objects.all()
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    serializer_class = AreaSerializer

  
class AreaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an area instance
    """
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    
    
class FacilityListCreateView(generics.ListCreateAPIView):
    """
    List all facilities or create a new facility.
    """
    queryset = Facility.objects.all()
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    serializer_class = FacilitySerializer

  
class FacilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a facility instance
    """
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    
    
    
    
class RouteListCreateView(generics.ListCreateAPIView):
    """
    List all routes or create a new route.
    """
    queryset = Route.objects.all()
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    serializer_class = RouteSerializer
 
    
    def perform_create(self, serializer):#code gotten from https://www.django-rest-framework.org/api-guide/generic-views/#get_serializer_classself
        serializer.save(owner=self.request.user)

class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a route instance
    """
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    from .serializers import GymSerializer, AreaSerializer, RouteSerializer, FacilitySerializer
from rest_framework import generics
from .models import Gym, Area, Route, Facility
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .permissions import IsOwnerOrReadOnly

class GymListCreateView(generics.ListCreateAPIView):
    """
    List all gyms or create a new gym.
    """
    queryset = Gym.objects.all()
    search_fields = ['name', 'address', 'facilities__name']
    ordering_fields = ['name', 'monthly_price']
    ordering = ['name']

    serializer_class = GymSerializer

  
class GymDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a gym instance
    """
    queryset = Gym.objects.all()
    serializer_class = GymSerializer

   
   
class AreaListCreateView(generics.ListCreateAPIView):
    """
    List all areas or create a new area.
    """
    queryset = Area.objects.all()
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    serializer_class = AreaSerializer

  
class AreaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an area instance
    """
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    
    
class FacilityListCreateView(generics.ListCreateAPIView):
    """
    List all facilities or create a new facility.
    """
    queryset = Facility.objects.all()
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    serializer_class = FacilitySerializer

  
class FacilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a facility instance
    """
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    
    
    
class RouteListCreateView(generics.ListCreateAPIView):
    """
    List all routes or create a new route.
    """
    queryset = Route.objects.all()
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    serializer_class = RouteSerializer
 
    
    def perform_create(self, serializer):#code gotten from https://www.django-rest-framework.org/api-guide/generic-views/#save-and-deletion-hook
        serializer.save(owner=self.request.user)


class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a route instance
    """
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]