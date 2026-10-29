from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Gym, Facility, Area, Route

# Opens the admin map centred on Dublin, with a text box for pasting coordinates
DUBLIN_MAP = {'attrs': {'default_lon': -6.26, 'default_lat': 53.35, 'default_zoom': 12, 'display_raw': True}}


@admin.register(Gym)
class GymAdmin(GISModelAdmin):
    list_display = ['name', 'opening_time', 'closing_time', 'is_24_hours_open', 'website', 'address', 'monthly_price']
    search_fields = ['name', 'facilities__name']
    gis_widget_kwargs = DUBLIN_MAP
    filter_horizontal = ['facilities']


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Area)
class AreaAdmin(GISModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    gis_widget_kwargs = DUBLIN_MAP


@admin.register(Route)
class RouteAdmin(GISModelAdmin):
    list_display = ['name', 'owner']
    search_fields = ['name']
    gis_widget_kwargs = DUBLIN_MAP