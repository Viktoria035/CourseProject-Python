from django.shortcuts import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login')
def index(request):
    """Welcome page."""
    return HttpResponse("Welcome!")