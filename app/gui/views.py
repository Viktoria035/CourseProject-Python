from typing import Any
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from app.functions import change_player_level_by_score, get_player_rank_in_leaderboard
from .models import Player, Quiz, Category, Question, Answer, QuestionResponse, QuizAttempt
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
        player = Player.objects.get(user=request.user)
        change_player_level_by_score(player=player)
        get_player_rank_in_leaderboard(player=player)
        
        context = {
            'username': request.user.username,
            'level': player.level,
            'score': player.score,
            'rank': player.rank,
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
def not_found(request):
    return render(request, 'question/not_found.html')

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
    quizzes = Quiz.objects.filter(category=Category.objects.get(category=category)).all()
    
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

    if quiz is None:
        return redirect('not_found')
    
    if request.method == "POST":
        question = Question.objects.filter(quiz=quiz).first()
        if question is None:
            return redirect('not_found')

        quiz_attempt = QuizAttempt(quiz=quiz)
        quiz_attempt.save()
        player = Player.objects.get(user=request.user)
        player.active_attempt = quiz_attempt
        player.save()
        
        if question.question_type == 'single choice':
            return redirect('view_single_choice_question', quiz_id=quiz_id, question_id=question.id)
        elif question.question_type == 'multiple choice':
            return redirect('view_multiple_choice_question', quiz_id=quiz_id, question_id=question.id)
    context = {
        'quiz': quiz
    }
    return render(request, 'question/view_quiz.html', context=context)

@login_required(login_url='\login')
def view_single_choice_question(request, quiz_id, question_id):
    print("you are in single choice question")
    quiz = Quiz.objects.filter(id=quiz_id).first()
    question = Question.objects.filter(id=question_id, quiz=quiz).first()
    next_question = Question.objects.filter(quiz=quiz, id__gt=question.id).first()

    if quiz is None or question is None:
        return redirect('not_found')
    
    if request.method == "POST":
        answer_response_id = request.POST.get('answer')
        if answer_response_id is None:
            messages.warning(request, 'You have to answer the question to proceed!')
            return redirect(request.path)
        answer = Answer.objects.filter(question=question, id=answer_response_id).first()
        player = Player.objects.get(user=request.user)
        question_response = QuestionResponse(
            player=player,
            quiz=quiz,
            question=question,
            answer=answer,
        )
        question_response.save()
        player.active_attempt.responses.add(question_response)
        
        if answer.is_correct:
            player.active_attempt.score += answer.points
            player.active_attempt.save()

        if next_question is None:
            return redirect('results', quiz_id=quiz_id)
        
        if next_question.question_type == 'single choice':
            return redirect('view_single_choice_question', quiz_id=quiz_id, question_id=next_question.id)
        elif next_question.question_type == 'multiple choice':
            return redirect('view_multiple_choice_question', quiz_id=quiz_id, question_id=next_question.id)
    else:
        answers = Answer.objects.filter(question=question).all()
        context = {
            'quiz': quiz, 
            'question': question,
            'no_next_question': next_question is None,
            'answers': answers
        }
        return render(request, 'question/single_choice_question.html', context=context)

@login_required(login_url='/login')
def view_multiple_choice_question(request, quiz_id, question_id):
    quiz = Quiz.objects.filter(id=quiz_id).first()
    question = Question.objects.filter(id=question_id, quiz=quiz).first()
    next_question = Question.objects.filter(quiz=quiz, id__gt=question.id).first()

    if quiz is None or question is None:
        return redirect('not_found')
    
    if request.method == "POST":
        answer_responses_id = request.POST.getlist('answer_responses_id')
        if len(answer_responses_id) == 0:
            messages.warning(request, 'You have to answer the question to proceed!')
            return redirect(request.path)
        answers = [Answer.objects.filter(question=question, id=answer_response_id).first() for answer_response_id in answer_responses_id]
        player = Player.objects.get(user=request.user)
        for answer in answers:
            question_response = QuestionResponse(
                player=player,
                quiz=quiz,
                question=question,
                answer=answer,
            )
            question_response.save()
            player.active_attempt.responses.add(question_response)
            
            if answer.is_correct:
                player.active_attempt.score += answer.points
                player.active_attempt.save()

        if next_question is None:
            return redirect('results', quiz_id=quiz_id)
        
        if next_question.question_type == 'single choice':
            return redirect('view_single_choice_question', quiz_id=quiz_id, question_id=next_question.id)
        elif next_question.question_type == 'multiple choice':
            return redirect('view_multiple_choice_question', quiz_id=quiz_id, question_id=next_question.id)
    else:
        answers = Answer.objects.filter(question=question).all()
        context = {
            'quiz': quiz, 
            'question': question,
            'no_next_question': next_question is None,
            'answers': answers
        }
        return render(request, 'question/multiple_choice_question.html', context=context)

@login_required(login_url='/login')
def results(request, quiz_id):
    quiz = Quiz.objects.filter(id=quiz_id).first()
    player = Player.objects.get(user=request.user)

    if quiz is None or player.active_attempt is None:
        return redirect('not_found')
    
    context = {
        'quiz': quiz,
        'quiz_attempt': player.active_attempt,
        'questions': [
            {
                'question': question_response.question,
                'answers': [answer for answer in Answer.objects.filter(question=question_response.question).all()],
                'user_answer': question_response.answer,
                'right_answer': Answer.objects.filter(question=question_response.question, is_correct=True).first()
            }
        for question_response in player.active_attempt.responses.all()]
    }
    
    player.score += player.active_attempt.score
    player.active_attempt = None
    player.save()
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