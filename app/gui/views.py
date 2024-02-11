from typing import Any
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
#from .forms import RegisterUserForm
from app.functions import calculate_leaderboard_rank
from .models import Player, Quiz, Category
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

# @login_required(login_url='/login')
def index(request):
    """Welcome page."""
    context = {}
    if request.user.is_authenticated:
        context = {
            'username': request.user.username,
            'level': Player.objects.get(user=request.user).level,
            'score': Player.objects.get(user=request.user).score,
            'rank': Player.objects.get(user=request.user).rank,
        }
    return render(request, 'question/index.html', context)

# def register(request):
#     if request.method == "POST":
#         form = RegisterUserForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             # username = form.cleaned_data.get('username')
#             # raw_password = form.cleaned_data.get('password1')
#             # user = authenticate(username=username, password=raw_password)
#             login(request, user)
#             return redirect(index)
#     else:
#         form = RegisterUserForm()

#     context = {
#         'form': form
#     }
#     return render(request, 'registration/register.html', context)

def register(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_c = request.POST.get("password-c")
        if (password == password_c):
            try:
                user = User.objects.create_user(username, email, password);
                user.save()
                Player(user=user).save()
                messages.success(request, "Account created")
                return redirect("login")
            except IntegrityError:
                messages.info(request, "Username taken, Try different")
                return render(request, "registration/register.html")
        messages.error(request, "Password doesn't match Confirm Password")
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, "registration/register.html")

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
    profiles = Player.objects.all().order_by('-score')

    context = {
        'profiles': profiles,
        'auth': request.user.is_authenticated
    }
    return render(request, 'question/leaderboard.html', context=context)

@login_required(login_url='/login')
def view_quiz_categories(request):
    """View quiz categories."""
    categories = Category.objects.all()
    context = {
        'categories': categories
    }
    return render(request, 'question/view_quiz_categories.html', context=context)


class QuizListView(ListView):
    model = Quiz
    template_name = 'quiz/quiz_list.html'

    def get_queryset(self):
        queryset = super(QuizListView, self).get_queryset()
        return queryset.filter(draft=False)


class QuizDetailView(DetailView):
    model = Quiz
    slug_field = 'url'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.draft and not request.user.has_perm('quiz.change_quiz'):
            raise PermissionDenied

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class CategoriesListView(ListView):
    model = Category


class ViewQuizListByCategory(ListView):
    model = Quiz
    template_name = 'question/view_quiz_categories.html'

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