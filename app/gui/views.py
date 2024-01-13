from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .forms import RegisterUserForm
from app.functions import calculate_leaderboard_rank

# @login_required(login_url='/login')
def index(request):
    """Welcome page."""

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

    return render(request, 'question/leaderboard.html')

