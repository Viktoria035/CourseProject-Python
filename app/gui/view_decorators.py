from django.http import HttpResponseNotFound

def can_view_item(model):
    def decorator(view):
        def decorated(request):
            try:
                id = int(getattr(request, request.method)['id'])
                object_ = model.objects.get(pk=id)
                if hasattr(object_, 'owner'):
                    if object_.player != request.user:
                        return HttpResponseNotFound('Invalid link.')
                elif object_.quiz.player != request.user:
                    return HttpResponseNotFound('Invalid link.')
            except (KeyError, ValueError, model.DoesNotExist):
                return HttpResponseNotFound('Invalid link.')
            return view(request)
        return decorated
    return decorator