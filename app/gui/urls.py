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
    path('quiz/<quiz_id>/question/<question_id>', views.view_question, name='view_question')
]