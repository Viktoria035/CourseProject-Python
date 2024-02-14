from typing import Any
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from app.functions import change_player_level_by_score, get_player_rank_in_leaderboard
from .models import Player, Quiz, Category, Question, Answer, QuestionResponse, QuizAttempt, Forum, Discussion ,QUESTION_TYPES
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from .forms import CategoryForm, QuizForm, QuestionForm, AnswerForm, CreateInForumForm, CreateInDiscussionForm

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
    return render(request, 'quiz/index.html', context)

def register(request):
    """Register page."""

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_c = request.POST.get('password-c')
        if (password == password_c):
            try:
                user = User.objects.create_user(username, email, password);
                user.save()
                Player(user=user).save()
                messages.success(request, 'Account created')
                return redirect('login')
            except IntegrityError:
                messages.info(request, 'Username taken, Try different')
                return render(request, 'registration/register.html')
        messages.error(request, "Password doesn't match Confirm Password")
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'registration/register.html')

@login_required(login_url='/login')
def rules(request):
    """Rules page."""

    return render(request, 'quiz/rules.html')

@login_required(login_url='/login')
def question(request):
    """Question page."""

    return render(request, 'quiz/question.html')

@login_required(login_url='/login')
def leaderboard(request):
    """Leaderboard page."""

    profiles = Player.objects.all().order_by('-score')

    context = {
        'profiles': profiles,
        'auth': request.user.is_authenticated
    }
    return render(request, 'quiz/leaderboard.html', context=context)

@login_required(login_url='/login')
def not_found(request):
    """Not found page."""

    return render(request, 'quiz/not_found.html')

@login_required(login_url='/login')
def view_quiz_categories(request):
    """View quiz categories."""

    categories = Category.objects.all()
    if categories is None:
        return redirect('not_found')
    
    context = {
        'categories': categories
    }
    return render(request, 'quiz/view_quiz_categories.html', context=context)

@login_required(login_url='/login')
def view_quizzes_by_category(request, category):
    """View quizzes by category."""

    quizzes = Quiz.objects.filter(category=Category.objects.get(category=category)).all()
    
    if quizzes is None:
        return redirect('not_found')
    
    context = {
        'quizzes': quizzes,
        'category': category
    }
    return render(request, 'quiz/view_quizzes_by_category.html', context=context)

@login_required(login_url='/login')
def view_quiz(request, quiz_id):
    """View quiz."""

    quiz = Quiz.objects.filter(id=quiz_id).first()

    if quiz is None:
        return redirect('not_found')
    
    if request.method == 'POST':
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
    return render(request, 'quiz/view_quiz.html', context=context)

@login_required(login_url='\login')
def view_single_choice_question(request, quiz_id, question_id):
    """View single choice question."""

    quiz = Quiz.objects.filter(id=quiz_id).first()
    question = Question.objects.filter(id=question_id, quiz=quiz).first()
    next_question = Question.objects.filter(quiz=quiz, id__gt=question.id).first()

    if quiz is None or question is None:
        return redirect('not_found')
    
    if request.method == 'POST':
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
        return render(request, 'quiz/single_choice_question.html', context=context)

@login_required(login_url='/login')
def view_multiple_choice_question(request, quiz_id, question_id):
    """View multiple choice question."""

    quiz = Quiz.objects.filter(id=quiz_id).first()
    question = Question.objects.filter(id=question_id, quiz=quiz).first()
    next_question = Question.objects.filter(quiz=quiz, id__gt=question.id).first()

    if quiz is None or question is None:
        return redirect('not_found')
    
    if request.method == 'POST':
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
        
        if next_question.question_type == QUESTION_TYPES[0][0]:
            return redirect('view_single_choice_question', quiz_id=quiz_id, question_id=next_question.id)
        elif next_question.question_type == QUESTION_TYPES[1][0]:
            return redirect('view_multiple_choice_question', quiz_id=quiz_id, question_id=next_question.id)
    else:
        answers = Answer.objects.filter(question=question).all()
        context = {
            'quiz': quiz, 
            'question': question,
            'no_next_question': next_question is None,
            'answers': answers
        }
        return render(request, 'quiz/multiple_choice_question.html', context=context)

@login_required(login_url='/login')
def results(request, quiz_id):
    """Results page."""

    quiz = Quiz.objects.filter(id=quiz_id).first()
    player = Player.objects.get(user=request.user)

    if quiz is None or player.active_attempt is None:
        return redirect('not_found')
    
    questions = Question.objects.filter(quiz=quiz)
    context = {
        'quiz': quiz,
        'quiz_attempt': player.active_attempt,
        'questions': [
            {
                'question': question,
                'answers': [answer for answer in Answer.objects.filter(question=question).all()],
                'user_answers': player.active_attempt.responses.filter(
                    quiz=quiz,
                    player=player,
                    question=question                
                ).all(),
                'right_answers': Answer.objects.filter(question=question, is_correct=True).all()
            }
            for question in questions
        ]
    }
    
    player.score += player.active_attempt.score
    player.active_attempt = None
    player.save()
    return render(request, 'quiz/result.html', context=context)

@login_required(login_url='/login')
def create(request):
    """Create page."""

    return render(request, 'create/create.html')

@login_required(login_url='/login')
def create_category(request):
    """Create category page."""

    form = CategoryForm()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category was successfully created. Continue with adding quiz/es')
            return redirect(request.path)
        else:
            messages.warning(request, 'Invalid form!')
            return redirect(request.path)
        
    context = {
        'form': form
    }
    return render(request, 'create/create_category.html', context=context)

@login_required(login_url='/login')
def create_quiz(request):
    """Create quiz page."""

    form = QuizForm()
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz was successfully added. Continue with adding question/s!')
            return redirect(request.path)
        else:
            messages.warning(request, 'Invalid form!')
            return redirect(request.path)
    context = {
        'form': form
    }
    return render(request, 'create/create_quiz.html', context=context)

@login_required(login_url='/login')
def create_question(request):
    """Create question page."""

    form = QuestionForm()
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question/s was/were successfully added. Continue with adding answer/s!')
            return redirect(request.path)
        else:
            messages.warning(request, 'Invalid form!')
            return redirect(request.path)
    context = {
        'form': form
    }
    return render(request, 'create/create_question.html', context=context)

@login_required(login_url='/login')
def create_answer(request):
    """Create answer page."""
    form = AnswerForm()
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Answer/s was/were successfully added.')
            return redirect(request.path)
        else:
            messages.warning(request, 'Invalid form!')
            return redirect(request.path)
    context = {
        'form': form
    }
    return render(request, 'create/create_answer.html', context=context)

@login_required(login_url='/login')
def forum_page(request):
    """Forum page."""

    forums = Forum.objects.all()
    count = forums.count()
    discussions = []
    for forum in forums:
        discussions.append(Discussion.objects.filter(forum=forum).all())

    context = {
        'forums': forums,
        'discussions': discussions,
        'count': count,
    }
    return render(request, 'forum/forum_page.html', context=context)

@login_required(login_url='/login')
def add_in_forum(request):
    """Add in forum page."""
    form = CreateInForumForm()
    if request.method == 'POST':
        form = CreateInForumForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Forum was successfully added.')
            return redirect(request.path)
    context = {
        'form': form
    }
    return render(request, 'forum/add_in_forum.html', context=context)

@login_required(login_url='/login')
def add_in_discussion(request):
    """Add in discussion page."""
    form = CreateInDiscussionForm()
    if request.method == 'POST':
        form = CreateInDiscussionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Discussion was successfully added.')
            return redirect(request.path)
    context = {
        'form': form
    }
    return render(request, 'forum/add_in_discussion.html', context=context)

@login_required(login_url='/login')
def edit(request):
    """Edit category page."""

    return render(request, 'forms/edit.html')

@login_required(login_url='/login')
def edit_quiz(request):
    """Edit quiz page."""

    pass

@login_required(login_url='/login')
def edit_question(request):
    """Edit question page."""

    pass

@login_required(login_url='/login')
def edit_answer(request):
    """Edit answer page."""

    pass

@login_required(login_url='/login')
def edit_category(request):
    """Edit category page."""

    if request.method == 'POST':
        category_title = request.POST.get('category')
        category = Category.objects.filter(category=category_title).first()
        if category is None:
            return redirect('not_found')
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category was successfully edited.')
            return redirect('edit_category', category_title=category.category)
        else:
            messages.warning(request, 'Invalid form!')
            return redirect('edit_category', category_title=category.category)
    return render(request, 'forms/edit_category.html', {'form': CategoryForm()})