from django.http.response import HttpResponse as HttpResponse
from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from app.functions import change_player_level_by_score, get_player_rank_in_leaderboard, get_plot_for_per_player_since_registration, get_plot_for_each_quiz_score
from .models import Player, Quiz, Category, Question, Answer, QuestionResponse, QuizAttempt, Forum, Discussion, PointsPerDay, QUESTION_TYPES, MultiPlayerSession
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import CategoryForm, QuizForm, QuestionForm, AnswerForm, CreateInForumForm, CreateInDiscussionForm
from datetime import date


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

# def password_reset(request):
#     """Password reset page."""

#     if request.method == 'POST':
#         email = request.POST.get('email')
#         user = User.objects.filter(email=email).first()
#         if user is not None:
#             password = request.POST.get('password')
#             password_c = request.POST.get('password-c')
#             if password == password_c:
#                 user.set_password(request.POST.get('password'))
#                 user.save()
#                 messages.success(request, 'Password reset successfully')
#                 return redirect('login')
#             else:
#                 messages.error(request, "Password doesn't match Confirm Password")
#                 return render(request, 'registration/password_reset.html')
#         messages.error(request, 'Email not found')

#     return render(request, 'registration/password_reset.html')

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

    if quiz is None:
        messages.error(request, 'Quiz does not exists.')
        return redirect('not_found')
    
    if request.method == 'POST' and request.POST.get('start-quiz'):
        question = Question.objects.filter(quiz=quiz).first()
        if question is None:
            messages.warning(request, 'No questions available for this quiz!')
            return redirect('not_found')

        quiz_attempt = QuizAttempt(quiz=quiz)
        quiz_attempt.save()
        player.active_attempt = quiz_attempt
        player.save()
        
        if question.question_type == 'single choice':
            return redirect('view_single_choice_question', quiz_id=quiz_id, question_id=question.id)
        elif question.question_type == 'multiple choice':
            return redirect('view_multiple_choice_question', quiz_id=quiz_id, question_id=question.id)
    elif request.method == 'POST' and request.POST.get('create-room'):
        room_code = request.POST.get('create-room-code')
        if room_code == '':
            messages.error(request, 'You have to enter a room code to join!')
            return redirect('view_quiz', quiz_id=quiz_id)
        multiplayer = MultiPlayerSession(room_code=room_code, quiz=quiz, creator=player)
        multiplayer.save()
        return redirect('multiplayer', room_code=multiplayer.room_code)
    elif request.method == 'POST' and request.POST.get('join-room'):
        room_code = request.POST.get('join-room-code')
        if room_code == '':
            messages.error(request, 'You have to enter a room code to join!')
            return redirect('view_quiz', quiz_id=quiz_id)
        multiplayer = MultiPlayerSession.objects.filter(room_code=room_code).first()
        if multiplayer is None:
            messages.warning(request, 'Room does not exist!')
            return redirect('not_found')
        return redirect('multiplayer', room_code=multiplayer.room_code)

    context = {
        'quiz': quiz
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

        """If the player has already answered the quiz, he can not return to the previous question. So we redirect him to the quiz page."""
        if player.active_attempt is None:
            messages.error(request, 'You can not return when you have already answer the quiz. Please, start new quiz.')
            return redirect('view_quiz', quiz_id=quiz_id)
        
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
    """Multiple choice question may has more than one correct answer, for every correct answer 
    given from the user the points are added to his profile."""

    quiz = Quiz.objects.filter(id=quiz_id).first()
    question = Question.objects.filter(id=question_id, quiz=quiz).first()

    if quiz is None or question is None:
        return redirect('not_found')
    
    next_question = Question.objects.filter(quiz=quiz, id__gt=question.id).first()
    
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
            
            """If the player has already answered the quiz, he can not return to the previous question. So we redirect him to the quiz page."""
            if player.active_attempt is None:
                messages.error(request, 'You can not return when you have already answer the quiz. Please, start new quiz.')
                return redirect('view_quiz', quiz_id=quiz_id)
            
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
    points_today = PointsPerDay.objects.get_or_create(player=player, date=date.today())[0]
    points_today.points += player.active_attempt.score
    points_today.save()
    player.active_attempt = None
    player.save()
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
        if form.is_valid():
            category = form.save(commit=False)
            category.player = Player.objects.get(user=request.user)
            category.save()
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
            quiz = form.save(commit=False)
            try:
                quiz.player = Player.objects.get(user=request.user)
            except Player.DoesNotExist:
                raise Http404("Player does not exist")
            quiz.save()
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
        quiz = Quiz.objects.get(id=request.POST.get('quiz'))
        question = request.POST.get('question')
        question_type = request.POST.get('question_type')
        player = Player.objects.get(user=request.user)
        if quiz.player != player:
            messages.error(request, 'You are not authorized to add question to this quiz!')
            return redirect('create_question')
        form = QuestionForm({
            'quiz': quiz,
            'question': question,
            'question_type': question_type
        })
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
        question = Question.objects.get(id=request.POST.get('question'))
        answer = request.POST.get('answer')
        points = request.POST.get('points')
        is_correct = request.POST.get('is_correct')
        player = Player.objects.get(user=request.user)
        if question.quiz.player != player:
            messages.error(request, 'You are not authorized to add answer to this question!')
            return redirect('create_answer')
        form = AnswerForm({
            'question': question,
            'answer': answer,
            'points': points,
            'is_correct': is_correct
        })
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
        if player == forum.player:
            forum.is_deleted = True
            forum.save()
            messages.success(request, 'Forum deleted successfully!')
        else:
            messages.error(request, 'You are not authorized to delete this category!')
    return redirect('forum_page')

@login_required(login_url='/login')
def add_in_forum(request):
    """Add in forum page."""

    form = CreateInForumForm()
    if request.method == 'POST':
        form = CreateInForumForm(request.POST)
        if form.is_valid():
            forum = form.save(commit=False)
            forum.player = Player.objects.get(user=request.user)
            forum.save()
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
            forum = form.cleaned_data['forum'] # we are retrieving the cleaned value for the 'forum' field from the submitted form data
            if not forum.is_deleted:
                form.save()
                messages.success(request, 'Discussion was successfully added.')
                return redirect(request.path)
            else:
                messages.error(request, 'Cannot add discussion to a deleted forum!')
                return redirect('add_in_discussion')
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

    if player != quiz.player:
        messages.error(request, 'You are not authorized to edit this quiz!')
        return redirect('quizzes_by_category', category=category)
    
    if request.method == "GET":
        form = QuizForm(instance=quiz)
        return render(request, 'create/edit_quiz.html', {'form': form})
    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully!')
            return redirect('quizzes_by_category', category=category)
        else:
            messages.error(request, 'Invalid form!')
            return redirect('edit_quiz', quiz_id=quiz_id, category=category)

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
def edit_question(request, question_id):
    """Edit question page."""
    
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        messages.error(request, 'Question does not exist!')
        return redirect('not_found')

    if request.method == "GET":
        form = QuestionForm(instance=question)
        return render(request, 'create/edit_question.html', {'form': form})
    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('show_all_questions_for_player')
        else:
            messages.error(request, 'Invalid form!')
            return redirect('edit_question', question_id=question_id)

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
def edit_answer(request, answer_id):
    """Edit answer page."""

    try:
        answer = Answer.objects.get(id=answer_id)
    except Answer.DoesNotExist:
        messages.error(request, 'Answer does not exist!')
        return redirect('not_found')
    
    if request.method == "GET":
        form = AnswerForm(instance=answer)
        return render(request, 'create/edit_answer.html', {'form': form})
    if request.method == "POST":
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Answer updated successfully!')
            return redirect('show_all_answers_for_player')
        else:
            messages.error(request, 'Invalid form!')
            return redirect('edit_answer', answer_id=answer_id)

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
        if player == category.player:
            category.is_deleted = True
            category.save()
            messages.success(request, 'Category deleted successfully!')
        else:
            messages.error(request, 'You are not authorized to delete this category!')
        return redirect('quiz_categories')

@login_required(login_url='/login')
def view_multiplayer(request, room_code):
    """Joins user to multiplayer game room."""
    player = Player.objects.get(user=request.user)
    multiplayer = MultiPlayerSession.objects.get(room_code=room_code)
    username = player.user.username
    quiz = multiplayer.quiz
    question = Question.objects.filter(quiz=quiz).first()

    context = {
        'room_code' : room_code, 
        'username' : username,
        'player' : player,
        'quiz' : quiz,
        'question' : question
        }
    return render(request, 'quiz/multiplayer.html' , context)

# Maybe unusable
# @login_required(login_url='/login')
# def render_question_template(request, question_id, quiz_id):
#     """Renders the question template for multiplayer game."""
#     question = Question.objects.get(id=question_id)
#     if question.question_type == 'single choice':
#         return redirect('view_single_choice_question', quiz_id=quiz_id, question_id=question.id)
#     elif question.question_type == 'multiple choice':
#         return redirect('view_multiple_choice_question', quiz_id=quiz_id, question_id=question.id)
#     else:
#         messages.error(request, 'Something went wrong!')
#     return redirect('not_found')