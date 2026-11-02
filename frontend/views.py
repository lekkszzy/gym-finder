from django.shortcuts import render


def map_view(request):
    """Render the main gym finder map page."""
    return render(request, 'map.html')