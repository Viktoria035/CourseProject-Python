from typing import Any
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from app.functions import calculate_leaderboard_rank
from .models import Player, Quiz, Category, Question, Answer, QuestionResponse, Attempt, QuizAttempt
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

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
    if categories is None:
        return redirect('not_found')
    
    context = {
        'categories': categories
    }
    return render(request, 'question/view_quiz_categories.html', context=context)

@login_required(login_url='/login')
def view_quizzes_by_category(request, category):
    quizzes = Quiz.objects.filter(category=Category(category=category)).all()
    
    if quizzes is None:
        return redirect('not_found')
    
    context = {
        'quizzes': quizzes,
        'category': category
    }
    return render(request, 'question/view_quizzes_by_category.html', context=context)

@login_required(login_url='/login')
def view_quiz(request, quiz_id):
    quiz = Quiz.objects.filter(id=quiz_id).first()
    question = Question.objects.filter(quiz=quiz).first()

    if quiz is None or question is None:
        return redirect('not_found')
    
    if request.method == "POST":
        attempt = Attempt(
            player=Player.objects.get(user=request.user),
            quiz=quiz
        )
        attempt.save()
        # check this
        quiz_attempt = QuizAttempt(
            player=Player.objects.get(user=request.user),
            quiz=quiz,
        )
        quiz_attempt.save()
        quiz_attempt.attempt.add(attempt)
        return redirect('view_question', quiz_id=quiz_id, question_id=question.id)
    context = {
        'quiz': quiz
    }
    return render(request, 'question/view_quiz.html', context=context)

@login_required(login_url='/login')
def not_found(request):
    return render(request, 'question/not_found.html')

@login_required(login_url='\login')
def view_question(request, quiz_id, question_id):
    quiz = Quiz.objects.filter(id=quiz_id).first()
    question = Question.objects.filter(id=question_id, quiz=quiz).first()

    if quiz is None or question is None:
        return redirect('not_found')
    
    if request.method == "POST":
        print(request.POST)
        answer_response_id = request.POST.get('answer')
        answer = Answer.objects.filter(question=question, id=answer_response_id).first()
        attempt = Attempt.objects.filter(quiz=quiz, player=Player.objects.get(user=request.user)).first()
        quiz_attempt = QuizAttempt.objects.filter(player=Player.objects.get(user=request.user), quiz=quiz, attempt=attempt).first()
        player = Player.objects.get(user=request.user)
        question_response = QuestionResponse(
            player=player,
            quiz=quiz,
            question=question,
            answer=answer,
        )
        question_response.save()
        question_response.quiz_attempt.add(quiz_attempt)
        
        if answer.is_correct:
            attempt.score += answer.points
            attempt.answers.add(answer)
            player.score += answer.points
            player.save()
            attempt.save()

        next_question = Question.objects.filter(quiz=quiz, id__gt=question.id).first()
        if next_question is None:
            return redirect('results', quiz_id=quiz_id)
        return redirect('view_question', quiz_id=quiz_id, question_id=next_question.id)
    else:
        answers = Answer.objects.filter(question=question).all()
        context = {
            'quiz': quiz, 
            'question': question,
            'answers': answers,
        }
        return render(request, 'question/question.html', context=context)

@login_required(login_url='/login')
def results(request, quiz_id):
    quiz = Quiz.objects.filter(id=quiz_id).first()
    attempt = Attempt.objects.filter(quiz=quiz, player=Player.objects.get(user=request.user)).first()
    quiz_attempt = QuizAttempt.objects.filter(player=Player.objects.get(user=request.user), quiz=quiz, attempt=attempt).first()

    if quiz is None or attempt is None or quiz_attempt is None:
        return redirect('not_found')
    
    context = {
        'quiz': quiz,
        'quiz_attempt': quiz_attempt,
        'attempt': attempt,
        'questions': [
            {
                'question': question_response.question,
                'answers': [answer for answer in Answer.objects.filter(question=question_response.question).all()],
                'user_answer': question_response.answer,
                'right_answer': [answer for answer in Answer.objects.filter(question=question_response.question, is_correct=True).all()][0]
            }
        for question_response in QuestionResponse.objects.filter(quiz=quiz, player=Player.objects.get(user=request.user), quiz_attempt=quiz_attempt).all()]
    }
    return render(request, 'question/result.html', context=context)

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