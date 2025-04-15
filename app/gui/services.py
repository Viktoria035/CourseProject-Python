
from gui.models import Player, QuizAttempt, Question, MultiPlayerSession, Answer, QuestionResponse, PointsPerDay, QuestionType
from gui.forms import QuizForm, QuestionForm, AnswerForm
from django.contrib import messages
from django.shortcuts import redirect, render
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import date
from django.http import Http404

def get_player_rank_in_leaderboard(player):
    leaderboard = Player.objects.all().order_by('-score')

    rank = 1
    for p in leaderboard:
        if p == player:
            player.rank = rank
            break
        rank += 1

def change_player_level_by_score(player):
    if player.score < 0:
        player.level = 'Noob'
    elif 0 <= player.score <= 10:
        player.level = 'Beginner'
    elif 10 < player.score <= 20:
        player.level = 'Medium'
    elif 20 < player.score <= 30:
        player.level = 'Good'
    elif 30 < player.score <= 40:
        player.level = 'Very good'
    elif 40 < player.score <= 50:
        player.level = 'Impressive'
    elif 50 < player.score <= 60:
        player.level = 'Fighting for the top'
    else:
        player.level = 'Master'

def get_graph():
    """Function that generates a graph using matplotlip, save it as a PNG in memory, encode it into 
    base64 format, and then return the base64 encoded string representation of the image."""

    buffer = BytesIO() # creates an in-memory buffer
    plt.savefig(buffer, format='png') # saves the current matplotlib figure to the buffer in PNG format
    buffer.seek(0) # moves the pointer of the buffer back to the beginning, to read it from the start.
    image_png = buffer.getvalue() # reads the content of the buffer
    graph = base64.b64encode(image_png) # encodes the content of the buffer into base64 format
    graph = graph.decode('utf-8') # converts the base64 encoded bytes to a UTF-8 string representation
    buffer.close() # closes the buffer to free up system resources
    return graph

def plot_decorator(func):
    def wrapper(x, y, title, x_label, y_label):
        plt.switch_backend('AGG') # switches the backend of matplotlib to 'AGG', which is a non-interactive backend that is often used when generating plots without displaying them directly
        plt.figure(figsize=(10, 5)) # creates a new figure with a width of 10 inches and a height of 5 inches
        plt.title(title, fontsize=25, fontname="Baskerville Old Face")
        func(x, y)
        plt.xticks(rotation=45)
        plt.xlabel(x_label, fontsize=15, fontname="Baskerville Old Face")
        plt.ylabel(y_label, fontsize=15, fontname="Baskerville Old Face")
        plt.tight_layout()
        graph = get_graph()
        plt.close()
        return graph
    return wrapper

@plot_decorator
def get_plot_for_per_player_since_registration(x, y):
    plt.bar(x, y, color='orange', edgecolor='black')

@plot_decorator
def get_plot_for_each_quiz_score(x, y):
    plt.scatter(x, y, c='orange')
    plt.grid(True)

def start_quiz(request, quiz, player):
    question = Question.objects.filter(quiz=quiz).first()
    if question is None:
        messages.warning(request, 'No questions available for this quiz!')
        return redirect('not_found')

    quiz_attempt = QuizAttempt(quiz=quiz)
    quiz_attempt.save()
    player.active_attempt = quiz_attempt
    player.save()
        
    if question.question_type == QuestionType.SINGLE_CHOICE.value:
        return redirect('view_single_choice_question', quiz_id=quiz.id, question_id=question.id)
    elif question.question_type == QuestionType.MULTIPLE_CHOICE.value:
        return redirect('view_multiple_choice_question', quiz_id=quiz.id, question_id=question.id)
    
def create_room(request, quiz, player):
    room_code = request.POST.get('create-room-code')
    if room_code == '':
        messages.error(request, 'You have to enter a room code to join!')
        return redirect('view_quiz', quiz_id=quiz.id)

    if MultiPlayerSession.objects.filter(room_code=room_code, active=True).exists():
        messages.error(request, 'Room code already exists! Please enter a different one.')
        return redirect('view_quiz', quiz_id=quiz.id)

    multiplayer = MultiPlayerSession(room_code=room_code, quiz=quiz, creator=player, active=True)
    multiplayer.save()
    return redirect('multiplayer', room_code=multiplayer.room_code)

def join_room(request, quiz, player):
    room_code = request.POST.get('join-room-code')
    if room_code == '':
        messages.error(request, 'You have to enter a room code to join!')
        return redirect('view_quiz', quiz_id=quiz.id)
    
    multiplayer = MultiPlayerSession.objects.filter(room_code=room_code).first()
    if multiplayer is None:
        messages.warning(request, 'Room does not exist!')
        return redirect('not_found')
    
    if player in multiplayer.players.all():
        messages.warning(request, 'You are already in the room!')
        return redirect('not_found')
    
    if multiplayer.players.count() == 5:
        messages.warning(request, 'Room is full! Please enter another one.')
        return redirect('view_quiz', quiz_id=quiz.id)
    
    if multiplayer.started:
        messages.warning(request, 'Room is already started! Please enter another one.')
        return redirect('view_quiz', quiz_id=quiz.id)
        
    return redirect('multiplayer', room_code=multiplayer.room_code)

def create_question_response_and_update_score(question, answer_response_id, player, quiz):
    answer = Answer.objects.filter(question=question, id=answer_response_id).first()
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

def single_choice_answer(request, quiz, question, next_question):
    answer_response_id = request.POST.get('answer_response_id')
    
    if answer_response_id is None:
        messages.warning(request, 'You have to answer the question to proceed!')
        return redirect(request.path)
    
    player = Player.objects.get(user=request.user)
    
    """If the player has already answered the quiz, he can not return to the previous question. So we redirect him to the quiz page."""
    if player.active_attempt is None:
        messages.error(request, 'You can not return when you have already answer the quiz. Please, start new quiz.')
        return redirect('view_quiz', quiz_id=quiz.id)
    
    create_question_response_and_update_score(question=question, answer_response_id=answer_response_id, player=player, quiz=quiz)
    player.save()

    return get_next_question(quiz, next_question)

def multiple_choice_answer(request, quiz, question, next_question):
    answer_responses_id = request.POST.getlist('answer_response_id')
    
    if not answer_responses_id:
        messages.warning(request, 'You have to answer the question to proceed!')
        return redirect(request.path)
    
    player = Player.objects.get(user=request.user)
    
    """If the player has already answered the quiz, he can not return to the previous question. So we redirect him to the quiz page."""
    if player.active_attempt is None:
        messages.error(request, 'You can not return when you have already answer the quiz. Please, start new quiz.')
        return redirect('view_quiz', quiz_id=quiz.id)

    for answer_response_id in answer_responses_id:
        create_question_response_and_update_score(question=question, answer_response_id=answer_response_id, player=player, quiz=quiz)
    player.save()

    return get_next_question(quiz, next_question)
    
def get_next_question(quiz, next_question):
    if next_question is None:
        return redirect('results', quiz_id=quiz.id)
        
    if next_question.question_type == QuestionType.SINGLE_CHOICE.value:
        return redirect('view_single_choice_question', quiz_id=quiz.id, question_id=next_question.id)
    elif next_question.question_type == QuestionType.MULTIPLE_CHOICE.value:
        return redirect('view_multiple_choice_question', quiz_id=quiz.id, question_id=next_question.id)
    
def get_question_data_results(question, player, quiz):
    """Function that returns the question data for the results page."""
    return {
        'question': question,
        'answers': list(Answer.objects.filter(question=question)),
        'user_answers': player.active_attempt.responses.filter(
            quiz=quiz,
            player=player,
            question=question                
        ).all(),
        'right_answers': Answer.objects.filter(question=question, is_correct=True).all()
    }

def calculate_points_after_quiz(player):
    """Function that calculates the points after a quiz. The points are added to the player score and to the PointsPerDay model."""
    if player.active_attempt is None:
        return redirect('not_found')
    
    player.score += player.active_attempt.score
    points_today = PointsPerDay.objects.get_or_create(player=player, date=date.today())[0]
    points_today.points += player.active_attempt.score
    points_today.save()

    player.active_attempt = None
    player.save()

def edit_quiz_form(request, quiz):
    """Function that renders the edit quiz form. It is used in the edit_quiz view."""
    form = QuizForm(instance=quiz)
    return render(request, 'create/edit_quiz.html', {'form': form})

def edit_question_form(request, question):
    """Function that renders the edit question form. It is used in the edit_question view."""
    form = QuestionForm(instance=question)
    return render(request, 'create/edit_question.html', {'form': form})

def edit_answer_form(request, answer):
    """Function that renders the edit answer form. It is used in the edit_answer view."""
    form = AnswerForm(instance=answer)
    return render(request, 'create/edit_answer.html', {'form': form})

def edit_quiz_submission(request, quiz, category):
    """Function that handles the edit quiz form submission. It is used in the edit_quiz view."""
    if quiz.category.is_deleted:
        messages.error(request, 'You can not edit a quiz from a deleted category!')
        return redirect('not_found')
    
    form = QuizForm(request.POST, instance=quiz)
    return check_if_form_is_valid(request, form, 'Quiz updated successfully!', 'show_all_quizzes_for_player')
    
def edit_question_submission(request, question):
    """Function that handles the edit question form submission. It is used in the edit_question view."""
    player = Player.objects.get(user=request.user)

    if question.quiz.player != player:
        messages.error(request, 'You can not edit a question that does not belong to you!')
        return redirect('not_found')

    if question.quiz.category.is_deleted:
        messages.error(request, 'You can not edit a question from a deleted category!')
        return redirect('not_found')
    
    form = QuestionForm(request.POST, instance=question)
    return check_if_form_is_valid(request, form, 'Question updated successfully!', 'show_all_questions_for_player')
    
def edit_answer_submission(request, answer):
    """Function that handles the edit answer form submission. It is used in the edit_answer view."""
    player = Player.objects.get(user=request.user)

    if answer.question.quiz.player != player:
        messages.error(request, 'You can not edit an answer that does not belong to you!')
        return redirect('not_found')
    
    if answer.question.quiz.category.is_deleted:
        messages.error(request, 'You can not edit an answer from a deleted category!')
        return redirect('not_found')
    
    form = AnswerForm(request.POST, instance=answer)
    return check_if_form_is_valid(request, form, 'Answer updated successfully!', 'show_all_answers_for_player')
    
def check_if_form_is_valid(request, form, message, redirect_success_url):
    if form.is_valid():
        form.save()
        messages.success(request, message)
        return redirect(redirect_success_url)
    else:
        messages.error(request, 'Invalid form!')
        return redirect(request.path)
    
def check_if_form_is_valid_with_player(request, form, message, redirect_success_url):
    if form.is_valid():
        element = form.save(commit=False)
        try:
            element.player = Player.objects.get(user=request.user)
        except Player.DoesNotExist:
            raise Http404("Player does not exist")
        element.save()
        messages.success(request, message)
        return redirect(redirect_success_url)
    else:
        messages.warning(request, 'Invalid form!')
        return redirect(request.path)
    
def forum_disscussion_check(request, form, message, redirect_success_url):
    if form.is_valid():
        forum = form.cleaned_data['forum'] # we are retrieving the cleaned value for the 'forum' field from the submitted form data
        if not forum.is_deleted:
            return check_if_form_is_valid(request, form=form, message=message, redirect_success_url=redirect_success_url)
        else:
            messages.error(request, 'Cannot add discussion to a deleted forum!')
    return redirect(request.path)

def check_form_for_correct_user(request, form, current_user, message, redirect_success_url):
    player = Player.objects.get(user=request.user)

    if current_user != player:
        messages.error(request, 'You are not authorized to add question to this quiz!')
        return redirect(request.path)

    return check_if_form_is_valid(request, form=form, message=message, redirect_success_url=redirect_success_url)

def delete_element(request, player, element, message):
    if player == element.player:
        element.is_deleted = True
        element.save()
        messages.success(request, message)
    else:
        messages.error(request, 'You are not authorized to delete!')
