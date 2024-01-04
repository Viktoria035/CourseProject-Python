from django.urls import path
from . import views 

urlpatterns = [
    path("", views.response, name="response"),
    path("api/get-quiz/", views.get_quiz, name="get_quiz")
]