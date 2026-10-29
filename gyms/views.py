from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework_gis.pagination import GeoJsonPagination

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
    pagination_class = GeoJsonPagination


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
    pagination_class = GeoJsonPagination


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
    pagination_class = GeoJsonPagination

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
    
    
    
def parse_search_parameters(data, include_radius=False):
    """
    Validate lat, lng (and radius_km if include_radius is True) from the request.
    Returns (values, None) if valid, or (None, 400 error response) if not.
    """
    try:
        lat = float(data["lat"])
        lng = float(data["lng"])
    except (KeyError, TypeError, ValueError):
        return None, Response(
            {"error": "Provide numeric lat and lng values."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    radius_km = None
    if include_radius:
        try:
            radius_km = float(data.get("radius_km", 5))  # Default radius is 5 km
        except (TypeError, ValueError):
            return None, Response(
                {"error": "radius_km must be a number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if not 51 <= lat <= 56 or not -11 <= lng <= -5:
        return None, Response(
            {"error": "Location must be in Ireland (latitude 51 to 56, longitude -11 to -5)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if include_radius and not 0 < radius_km <= 50:# max  50 km 
        return None, Response(
            {"error": "radius_km must be greater than 0 and no more than 50."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return (lat, lng, radius_km), None


@api_view(["GET"])
def nearest_gyms(request):
    """GET /api/gyms/nearest/?lat=53.3498&lng=-6.2603&limit=5"""
    parameters, error = parse_search_parameters(request.query_params)
    if error:
        return error

    lat, lng, _ = parameters

    try:
        limit = int(request.query_params.get("limit", 5))
    except (TypeError, ValueError):
        return Response({"error": "limit must be a whole number."}, status=status.HTTP_400_BAD_REQUEST)

    if not 1 <= limit <= 50:
        return Response({"error": "limit must be between 1 and 50."}, status=status.HTTP_400_BAD_REQUEST)

    search_point = Point(lng, lat, srid=4326)

    gyms = Gym.objects.nearest(search_point, limit)
    results = GymSerializer(gyms, many=True).data

    return Response({
        "search_point": {"lat": lat, "lng": lng},
        "total_found": len(results["features"]),
        "gyms": results,
    })

@api_view(["GET"])
def gyms_within_radius(request):
    """GET /api/gyms/within-radius/?lat=53.3498&lng=-6.2603&radius_km=5"""
    parameters, error = parse_search_parameters(request.query_params, include_radius=True)
    if error:
        return error

    lat, lng, radius_km = parameters
    search_point = Point(lng, lat, srid=4326)

    gyms = Gym.objects.within_radius(search_point, radius_km)
    results = GymSerializer(gyms, many=True).data

    return Response({
        "search_point": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "total_found": len(results["features"]),
        "gyms": results,
    })
    
    
@api_view(["GET"])
def gyms_in_area(request, pk):
    """GET /api/areas/<pk>/gyms/"""
    area = get_object_or_404(Area, pk=pk)    # returns a 404 if the area doesn't exist

    gyms = Gym.objects.in_area(area)                              
    results = GymSerializer(gyms, many=True).data                          

    return Response({
        "area": area.name,
        "total_found": len(results["features"]),
        "gyms": results,
    })
    
    
    
@api_view(["GET"])
def gyms_along_route(request, pk):
    """GET /api/routes/<pk>/gyms/?buffer_m=500"""
    route = get_object_or_404(Route, pk=pk)

    try:
       buffer_m = float(request.query_params.get("buffer_m", 500))                    
    except (TypeError, ValueError):
        return Response({"error": "buffer_m must be a number."}, status=status.HTTP_400_BAD_REQUEST)

    if not 0 < buffer_m <= 5000:
        return Response({"error": "buffer_m must be greater than 0 and no more than 5000."}, status=status.HTTP_400_BAD_REQUEST)

    gyms = Gym.objects.along_route(route, buffer_m)                          
    results = GymSerializer(gyms, many=True).data

    return Response({
        "route": route.name,
        "buffer_m": buffer_m,
        "total_found": len(results["features"]),
        "gyms": results,
    })