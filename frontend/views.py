from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView


def map_view(request):
    """Render the main gym finder map page."""
    return render(request, 'map.html')


class SignUpView(CreateView):
    """Let new users create an account (Django's built-in UserCreationForm)."""
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')