from django.shortcuts import HttpResponse

def index(request):
    """Welcome page."""
    return HttpResponse("Welcome!")