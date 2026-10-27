from django.contrib.gis.db import models
from django.core.validators import MinValueValidator
from django.contrib.gis.measure import Distance
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.auth.models import User


class GymManager(models.Manager):
    """Custom manager for Gym model with spatial queries"""

    def within_radius(self, point, radius_km):
        """Find Gyms within radius of a point"""
        return self.filter(
            location__distance_lte=(point, Distance(km=radius_km))
        )
    
    
    
    def nearest(self,point, limit=15):
        """Used to find the nearest gym to a given point with a limit of 15 gyms"""
        return  self.filter(location__isnull=False).annotate(
        distance=DistanceFunction("location", point)
    ).order_by("distance")[:limit] 
        
     
    def open_24_hours(self):
        """Used to find 24 hour gyms"""
        return self.filter(is_24_hours_open=True)
    
    def in_area(self, area):
        """This function is used to find the gyms within a given area."""
        return self.filter(location__within=area.boundary)
    
    def along_route(self, routes,buffer_m=500):
        """This function is used to find gyms along a given route."""
        route_path = route_path.transform(2157, clone=True)
        zone = route_path.buffer(buffer_m)   # 100 metres
        return self.filter(location__intersects=routes.path)
    
class Facility(models.Model):
    """
    The facility model shows what facilities a gym has. Can be used as a filter for users.
    """
    
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
   
   
class Gym(models.Model):
        """This model represents the gyms attributes like name, location, opening and closing times, and facilities."""
        
        name = models.CharField(max_length=200)
        location = models.PointField( srid=4326)
        opening_time = models.TimeField(null=True, blank=True)
        closing_time = models.TimeField(null=True, blank=True)
        is_24_hours_open = models.BooleanField(default=False)# checks if a gym is open for 24 hours
        facilities = models.ManyToManyField(Facility, related_name='gyms', blank=True)
        website = models.URLField(blank=True)
        address = models.CharField(max_length=400, blank=True)
        monthly_price =  models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], blank=True, null=True)
            
        objects = GymManager()
        
        class Meta:
            ordering = ['name']
            
        def __str__(self):
            return self.name
        
class Area(models.Model):
    """A named area of Dublin, stored as a polygon boundary."""

    name = models.CharField(max_length=200, unique=True)
    boundary = models.PolygonField(srid=4326)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
    
class Route(models.Model):
    """The route model represents a path a user can take to get to a gym"""
    name = models.CharField(max_length=200)
    path = models.LineStringField(srid=4326)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routes')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name