from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from .models import *
import random

def response(request):
    return HttpResponse("Hello from Django!")

def get_quiz(request):
    try:
        question_objs = Question.objects.all()
        data = []
        for question_obj in question_objs:
            data.append({
                "category":question_obj.category.categoty_name,
                "question":question_obj.question,
                "answer":question_obj.marks
            })
        
        payload = {'status':True, 'data':data}

        return JsonResponse(payload)
    except Exception as e:
        print(e)
        return HttpResponse("Something went wrong!")
    