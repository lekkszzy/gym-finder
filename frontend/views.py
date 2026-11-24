from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_control
from django.views.generic import CreateView


def map_view(request):
    """Render the main gym finder map page."""
    return render(request, 'map.html')


@cache_control(no_cache=True)
def service_worker(request):
    """
    Serve the service worker from the site root (/sw.js).
    A service worker only controls pages at or below its own URL, so serving it
    from /static/ would limit it to /static/. no_cache makes browsers always
    check for a new version.
    """
    return render(request, 'sw.js', content_type='application/javascript')


def offline_view(request):
    """Fallback page the service worker shows when there is no network."""
    return render(request, 'offline.html')


class SignUpView(CreateView):
    """Let new users create an account (Django's built-in UserCreationForm)."""
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')