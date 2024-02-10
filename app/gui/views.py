from typing import Any
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import RegisterUserForm
from app.functions import calculate_leaderboard_rank
from .models import Player, Quizz, Category
from django.views.generic import ListView
from django.shortcuts import get_object_or_404


# @login_required(login_url='/login')
def index(request):
    """Welcome page."""
    context = {}
    if request.user.is_authenticated:
        context = {
            'username': request.user.username,
            'level': request.user.player.level,
            'score': request.user.player.score,
            'rank': request.user.player.rank,
        }
    return render(request, 'question/index.html', context)

def register(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(index)
    else:
        form = RegisterUserForm()
    context = {
        'form': form
    }
    return render(request, 'registration/register.html', context)


@login_required(login_url='/login')
def rules(request):
    """Rules page."""

    return render(request, 'question/rules.html')

@login_required(login_url='/login')
def question(request):
    """Question page."""

    return render(request, 'question/question.html')


@login_required(login_url='/login')
def leaderboard(request):
    """Leaderboard page."""
    players = Player.objects.all().order_by('-score')

    context = {
        'players': players,
        'auth': request.user.is_authenticated
    }
    return render(request, 'question/leaderboard.html', context=context)


class ViewQuizListByCategory(ListView):
    model = Quizz
    template_name = 'question/quiz_category.html'

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, category=self.kwargs['category'])

        return super(ViewQuizListByCategory, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(ViewQuizListByCategory, self).get_context_data(**kwargs)
        context['category'] = self.category
        return context
    
    def get_queryset(self):
        queryset = self.category.quizz_set.all()
        return queryset