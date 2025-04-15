from django.http.response import HttpResponse as HttpResponse
from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .services import *
from .models import Player, Quiz, Category, Question, Answer, QuizAttempt, Forum, Discussion, PointsPerDay, MultiPlayerSession
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import CategoryForm, QuizForm, QuestionForm, AnswerForm, CreateInForumForm, CreateInDiscussionForm
from datetime import date
from django.http import JsonResponse
import json


def index(request):
    """Welcome page. Displays the user characteristics if logged in."""

    context = {}
    if request.user.is_authenticated:
        try:
            player = Player.objects.get(user=request.user)
        except Player.DoesNotExist:
            messages.error(request, 'Player does not exist!')
            return redirect('login')
    
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
    """Register page. Registration with username, email and password."""

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_c = request.POST.get('password-c')
        if password == password_c:
            try:
                user = User.objects.create_user(username, email, password);
                user.save()
                Player(user=user, registration_date=date.today()).save()
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
    """The quiz rules."""

    return render(request, 'quiz/rules.html')

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
    """All quiz categories."""

    categories = Category.get_not_deleted_instances()

    if not categories.exists():
        messages.warning(request, 'No existing categories.')
        return redirect('not_found')
    
    context = {
        'categories': categories
    }
    return render(request, 'quiz/view_quiz_categories.html', context=context)

@login_required(login_url='/login')
def view_quizzes_by_category(request, category):
    """All quizzes of the category."""

    try:
        quizzes = Quiz.objects.filter(category=Category.objects.get(category=category)).all()
    except Category.DoesNotExist:
        messages.warning(request, 'No existing quizzes for this category.')
        return redirect('not_found')
    
    context = {
        'quizzes': quizzes,
        'category': category
    }
    return render(request, 'quiz/view_quizzes_by_category.html', context=context)

@login_required(login_url='/login')
def view_quiz(request, quiz_id):
    """Show quiz and start the game. A response is received from the user and a QuizAttempt object is created to save current information of the game, 
    then we redirect to the next question(if one exists), which can be one choice or multiple choice, depending on the type of question."""

    quiz = Quiz.objects.filter(id=quiz_id).first()
    player = Player.objects.get(user=request.user)
    active_rooms = MultiPlayerSession.objects.filter(quiz=quiz, active=True).all()

    if quiz is None:
        messages.error(request, 'Quiz does not exists.')
        return redirect('not_found')
    
    if request.method == 'POST':
        if request.POST.get('start-quiz'):
            return start_quiz(request, quiz=quiz, player=player)
        elif request.POST.get('create-room'):
            return create_room(request, quiz=quiz, player=player)
        elif request.POST.get('join-room') or request.POST.get('join-active-room'):
            return join_room(request, quiz=quiz, player=player)

    context = {
        'quiz': quiz,
        'active_rooms': active_rooms
    }
    return render(request, 'quiz/view_quiz.html', context=context)


@login_required(login_url='\login')
def view_single_choice_question(request, quiz_id, question_id):
    """Single choice question has only one correct answer, if the user answers correctly the points are added to his profile."""

    quiz = Quiz.objects.filter(id=quiz_id).first()
    question = Question.objects.filter(id=question_id, quiz=quiz).first()

    if quiz is None or question is None:
        messages.error(request, 'Quiz or question does not exist!')
        return redirect('not_found')
    
    next_question = Question.objects.filter(quiz=quiz, id__gt=question.id).first()
    
    if request.method == 'POST':
        return single_choice_answer(request, quiz=quiz, question=question, next_question=next_question)
    
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
    """Multiple choice question may has more than one correct answer, for every correct answer 
    given from the user the points are added to his profile."""

    quiz = Quiz.objects.filter(id=quiz_id).first()
    question = Question.objects.filter(id=question_id, quiz=quiz).first()

    if quiz is None or question is None:
        return redirect('not_found')
    
    next_question = Question.objects.filter(quiz=quiz, id__gt=question.id).first()
    
    if request.method == 'POST':
        return multiple_choice_answer(request, quiz=quiz, question=question, next_question=next_question)
        
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
    """Function that displays the results after a game(quiz title, questions, answers, correct answers for each question and the given ones from the user)."""

    quiz = Quiz.objects.filter(id=quiz_id).first()
    try:
        player = Player.objects.get(user=request.user)
    except Player.DoesNotExist:
        raise Http404("Player does not exist")

    if quiz is None or player.active_attempt is None:
        return redirect('not_found')
    
    questions = Question.objects.filter(quiz=quiz)
    if not questions.exists():
        return redirect('not_found')
    
    question_results = []
    for question in questions:
        question_results.append(get_question_data_results(question, player, quiz))
    
    context = {
        'quiz': quiz,
        'quiz_attempt': player.active_attempt,
        'questions': question_results
    }

    calculate_points_after_quiz(player=player)

    return render(request, 'quiz/result.html', context=context)

@login_required(login_url='/login')
def view_statistics(request):
    """View statistics page."""

    return render(request, 'statistics/statistics.html')

@login_required(login_url='/login')
def view_statistics_for_per_player(request):
    """Statistic on points earned after the registration of the user in the server so far."""

    try:
        player = Player.objects.get(user=request.user)
    except Player.DoesNotExist:
        raise Http404("Player does not exist")
    
    points_per_days = PointsPerDay.objects.filter(player=player)
    days = [points_per_day.date for points_per_day in points_per_days]
    points = [points_per_day.points for points_per_day in points_per_days]
    chart = get_plot_for_per_player_since_registration(days, points, 
                                                       'Points Earned per Day Since Registration', 'Days Since Registration', 'Points Earned')
    context = {
        'chart': chart
    }
    return render(request, 'statistics/statistics_for_per_player.html', context=context)

@login_required(login_url='/login')
def view_statistics_for_each_quiz_score(request):
    """Statistic on points earned from the quiz attempts of the users for each quiz."""

    quiz_attemps = QuizAttempt.objects.all()
    quizzes = [quiz_attempt.quiz.title for quiz_attempt in quiz_attemps]
    scores = [quiz_attempt.score for quiz_attempt in quiz_attemps]
    chart = get_plot_for_each_quiz_score(quizzes, scores, 
                                        'Points earned from each quiz', 'Quizzes', 'Points Earned')
    context = {
        'chart': chart
    }
    return render(request, 'statistics/statistics_for_each_quiz_score.html', context=context)

@login_required(login_url='/login')
def create_edit_page(request):
    """Create and edit page."""

    return render(request, 'create/create_edit_page.html')

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
        # check_if_form_is_valid_and_set_creator
        return check_if_form_is_valid_with_player(request, form=form, message='Category was successfully created. Continue with adding quiz/es', redirect_success_url='create_quiz')
        
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
        return check_if_form_is_valid_with_player(request, form=form, message='Quiz was successfully added. Continue with adding question/s!', redirect_success_url='create_question')

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
        quiz = Quiz.objects.get(id=request.POST.get('quiz'))
        return check_form_for_correct_user(request, form=form, current_user=quiz.player, message='Question/s was/were successfully added. Continue with adding answer/s!', redirect_success_url='create_answer')
        
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
        question = Question.objects.get(id=request.POST.get('question'))
        return check_form_for_correct_user(request, form=form, current_user=question.quiz.player, message='Answer/s was/were successfully added.', redirect_success_url='create')
        
    context = {
        'form': form
    }
    return render(request, 'create/create_answer.html', context=context)

@login_required(login_url='/login')
def forum_page(request):
    """Forum page."""

    forums = Forum.get_not_deleted_forums()
    count = len(forums)
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
def delete_forum_page(request, forum_id):
    """Delete forum page."""

    try:
        player = Player.objects.get(user=request.user)
        forum = Forum.objects.get(id=forum_id)
    except Player.DoesNotExist:
        raise Http404("Player does not exist")
    except Forum.DoesNotExist:
        messages.error(request, 'Forum does not exist!')
        return redirect('forum_page')
    
    if request.method == 'GET':
        delete_element(request, player=player, element=forum, message='Forum deleted successfully!')

    return redirect('forum_page')

@login_required(login_url='/login')
def add_in_forum(request):
    """Add in forum page."""

    form = CreateInForumForm()
    if request.method == 'POST':
        form = CreateInForumForm(request.POST)
        return check_if_form_is_valid_with_player(request, form=form, message='Forum was successfully added.', redirect_success_url='forum_page')
    
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
        #виж
        return forum_disscussion_check(request, form=form, message='Discussion was successfully added.', redirect_success_url='forum_page')

    context = {
        'form': form
    }
    return render(request, 'forum/add_in_discussion.html', context=context)

@login_required(login_url='/login')
def edit(request):
    """Edit page."""

    return render(request, 'create/edit.html')

@login_required(login_url='/login')
def edit_quiz(request, quiz_id, category):
    """Edit quiz page."""

    if category == None or quiz_id == None:
        return redirect('not_found')
    
    player = Player.objects.get(user=request.user)
    
    quiz = Quiz.objects.get(id=quiz_id)
    # виж какво можеш да ги направиш
    if player != quiz.player:
        messages.error(request, 'You are not authorized to edit this quiz!')
        return redirect('quizzes_by_category', category=category)

    if request.method == "GET":
        return edit_quiz_form(request, quiz=quiz)
    
    if request.method == "POST":
        return edit_quiz_submission(request, quiz=quiz, category=category)
    
@login_required(login_url='/login')
def edit_question(request, question_id):
    """Edit question page."""
    
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        messages.error(request, 'Question does not exist!')
        return redirect('not_found')
    
    player = Player.objects.get(user=request.user)

    if player != question.quiz.player:
        messages.error(request, 'You are not authorized to edit this question!')
        return redirect('quizzes_by_category', category=question.quiz.category.category)

    if request.method == "GET":
        return edit_question_form(request, question=question)
    
    if request.method == "POST":
        return edit_question_submission(request, question=question)
        
@login_required(login_url='/login')
def edit_answer(request, answer_id):
    """Edit answer page."""

    try:
        answer = Answer.objects.get(id=answer_id)
    except Answer.DoesNotExist:
        messages.error(request, 'Answer does not exist!')
        return redirect('not_found')
    
    player = Player.objects.get(user=request.user)
    if player != answer.question.quiz.player:
        messages.error(request, 'You are not authorized to edit this answer!')
        return redirect('quizzes_by_category', category=answer.question.quiz.category.category)
    
    if request.method == "GET":
        return edit_answer_form(request, answer=answer)
    
    if request.method == "POST":
        return edit_answer_submission(request, answer=answer)
        
@login_required(login_url='/login')
def show_all_quizzes_for_player(request):
    """Show all created quizzes from the user."""

    try:
        player = Player.objects.get(user=request.user)
    except Player.DoesNotExist:
        raise Http404("Player does not exist")
    quizzes = Quiz.quizzes_for_player(player_instance=player)

    context = {
        'quizzes': quizzes
    }
    return render(request, 'create/show_all_quizzes_for_player.html', context=context)

@login_required(login_url='/login')
def show_all_questions_for_player(request):
    """Show all created questions from the user."""

    try:
        player = Player.objects.get(user=request.user)
    except Player.DoesNotExist:
        raise Http404("Player does not exist")
    questions = Question.questions_for_player_in_quiz(player_instance=player)

    context = {
        'questions': questions
    }
    return render(request, 'create/show_all_questions_for_player.html', context=context)

@login_required(login_url='/login')
def show_all_answers_for_player(request):
    """Show all created answers from the user."""

    try:
        player = Player.objects.get(user=request.user)
    except Player.DoesNotExist:
        raise Http404("Player does not exist")
    answers = Answer.answers_for_player_in_quiz(player_instance=player)
    context = {
        'answers': answers
    }
    return render(request, 'create/show_all_answers_for_player.html', context=context)

@login_required(login_url='/login')
def delete_category(request, category_id):
    """Delete category page."""

    try:
        player = Player.objects.get(user=request.user)
        category = Category.objects.get(id=category_id)
    except Player.DoesNotExist:
        raise Http404("Player does not exist")
    except Category.DoesNotExist:
        messages.error(request, 'Category does not exist!')
        return redirect('not_found')
    
    if request.method == 'GET':
        delete_element(request, player=player, element=category, message='Category deleted successfully!')

    return redirect('quiz_categories')

@login_required(login_url='/login')
def view_multiplayer(request, room_code):
    """Joins user to multiplayer game room."""
    player = Player.objects.get(user=request.user)
    multiplayer = MultiPlayerSession.objects.get(room_code=room_code)
    username = player.user.username
    quiz = multiplayer.quiz
    is_creator = multiplayer.creator == player

    context = {
        'room_code' : room_code, 
        'username' : username,
        'player' : player,
        'quiz' : quiz,
        'is_creator': is_creator
        }
    return render(request, 'quiz/multiplayer.html' , context)
    
@login_required(login_url='/login')
def multiplayer_leaderboard(request):
    """Multiplayer leaderboard page."""

    results = request.GET.get('results', '[]')
    results = json.loads(results)
    context = {
        'results': results
    }
    return render(request, 'quiz/multiplayer_leaderboard.html', context=context)
