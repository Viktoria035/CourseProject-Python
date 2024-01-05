from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(login_url='/login')
def index(request):
    """Welcome page."""
    return render(request, 'index.html')