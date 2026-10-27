from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Gym, Facility, Area, Route


@admin.register(Gym)
class GymAdmin(GISModelAdmin):
    list_display = ['name', 'opening_time', 'closing_time', 'is_24_hours_open', 'website', 'address', 'monthly_price']
    search_fields = ['name','facilities__name']
    
@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']
    
@admin.register(Area)
class AreaAdmin(GISModelAdmin):
    list_display = ['name']
    search_fields = ['name']    
    
@admin.register(Route)
class RouteAdmin(GISModelAdmin):    
    list_display = ['name']
    search_fields = ['name']    