from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Gym, Facility, Area, Route


class FacilitySerializer(serializers.ModelSerializer):
    """Serializer for Facility model"""
    
    class Meta:
        model = Facility
        fields = ['id', 'name', 'description']
        
class GymSerializer(GeoFeatureModelSerializer):
    """Serializer for Gym model"""
    
    facilities = FacilitySerializer(many=True, read_only=True)
    
    class Meta:
        model = Gym
        geo_field = 'location'
        fields = ['id', 'name', 'location', 'opening_time', 'closing_time', 'is_24_hours_open', 'facilities', 'website', 'address', 'monthly_price']
        
class AreaSerializer(GeoFeatureModelSerializer):
    """Serializer for Area model"""
    
    class Meta:
        model = Area
        geo_field = 'boundary'
        fields = ['id', 'name', 'boundary'] 
        
class RouteSerializer(GeoFeatureModelSerializer):
    """Serializer for Route model"""
    owner = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
        model = Route
        geo_field = 'path'
        fields = ['id', 'name', 'path','owner']        