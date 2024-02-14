from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', auth_views.LoginView.as_view(), name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('register', views.register, name='register'),
    path('rules', views.rules, name='rules'),
    path('question', views.question, name='question'),
    path('leaderboard', views.leaderboard, name='leaderboard'),
    path('not_found', views.not_found, name='not_found'),
    path('quiz_categories', views.view_quiz_categories, name='quiz_categories'),
    path('quiz_categories/<category>', views.view_quizzes_by_category, name='quizzes_by_category'),
    path('quiz/<quiz_id>', views.view_quiz, name='view_quiz'),
    path('quiz/<quiz_id>/single_choice_question/<question_id>', views.view_single_choice_question, name='view_single_choice_question'),
    path('quiz/<quiz_id>/multiple_choice_question/<question_id>', views.view_multiple_choice_question, name='view_multiple_choice_question'),
    path('results/<quiz_id>', views.results, name='results'),
    path('create', views.create, name='create'),
    path('create_category', views.create_category, name='create_category'),
    path('create_quiz', views.create_quiz, name='create_quiz'),
    path('create_question', views.create_question, name='create_question'),
    path('create_answer', views.create_answer, name='create_answer'),
]