from django.http import HttpResponse

# Create your views here.

def response(request):
    return HttpResponse("Hello from Django!")