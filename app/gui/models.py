from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from django.core.validators import MaxValueValidator
import re
from datetime import date
# Create your models here.

DIFF_CHOICES = (
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
)

QUESTION_TYPES = (
    ('single choice', 'Single Choice'),
    ('multiple choice', 'Multiple Choice'),
)

class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    score = models.IntegerField(default=0, verbose_name=_("Score"))
    rank = models.IntegerField(default=0, verbose_name=_("Rank"))
    level = models.CharField(max_length=200, default='Beginner', verbose_name=_("Level"))
    active_attempt = models.ForeignKey('QuizAttempt', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Active Attempt"))
    registration_date = models.DateField(default=date.today, verbose_name=_("Registration Date"))

    def __str__(self):
        return self.user.username


class Category(models.Model):

    category = models.CharField(max_length=100, unique=True, null=True, verbose_name=_("Category"))
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, verbose_name=_("Creator"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
    
    @staticmethod
    def get_not_deleted_instances():
        not_deleted_instances = Category.objects.filter(is_deleted=False)
        return not_deleted_instances

    def __str__(self):
        return self.category
    

class Quiz(models.Model):

    title = models.CharField(max_length=100, blank=False, verbose_name=_("Title"))

    description = models.TextField(blank=True, help_text=_("A brief description of the quiz"), verbose_name=_("Description"))

    difficulty = models.CharField(max_length=6, choices=DIFF_CHOICES, default='easy', verbose_name=_("Difficulty"))

    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Category"))
    
    player = models.ForeignKey(Player,on_delete=models.CASCADE, help_text=_("The player who created the quiz."), verbose_name=_("Player"), null=True)

    max_questions = models.PositiveIntegerField(blank=True, null=True, help_text=_("Number of questions to be answered on each attempt"), verbose_name=_("Max Questions"))

    pass_mark = models.SmallIntegerField(blank=True, default=0, help_text=_("Percentage required to pass. Leave empty if no pass mark is required"), 
                                         validators=[MaxValueValidator(100)], verbose_name=_("Pass Mark"))


    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return f"{self.title} - {self.category} - {self.difficulty}"

    def get_questions(self):
        return self.question_set.all()[:self.max_questions] # we use the max_questions to limit the number of questions to be displayed


class Question(models.Model):
    question = models.CharField(max_length=200, verbose_name=_("Question"))
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name=_("Quiz"))
    created = models.DateTimeField(auto_now_add=True)
    question_type = models.CharField(max_length=15, choices=QUESTION_TYPES, default='single choice', verbose_name=_("Question Type"))

    def __str__(self):
        return self.question
    
    @staticmethod
    def questions_for_player_in_quiz(player_instance):
        return list(Question.objects.filter(quiz__player=player_instance, quiz__category__is_deleted=False))


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_("Question"))
    answer = models.CharField(max_length=200, verbose_name=_("Answer"))
    created = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField(default=1, verbose_name=_("Points"))
    is_correct = models.BooleanField(default=False, verbose_name=_("Is Correct"))

    @staticmethod
    def answers_for_player_in_quiz(player_instance):
        return list(Answer.objects.filter(question__quiz__player=player_instance, question__quiz__category__is_deleted=False))

    def __str__(self):
        return f"{self.answer} - {self.points}"
    

class QuestionResponse(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name=_("Player"))
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name=_("Quiz"))
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_("Question"))
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, verbose_name=_("Answer"))
    
    def is_correct(self):
        return self.answer.is_correct

    def __str__(self):
        return self.answer.answer


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name=_("Quiz"))
    date = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0, verbose_name=_("Score"))
    responses = models.ManyToManyField(QuestionResponse, verbose_name=_("Responses"))

    def __str__(self):
        return f" - {self.quiz.title}"
    

class PointsPerDay(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name=_("Player"))
    date = models.DateField(default=date.today, verbose_name=_("Date"))
    points = models.IntegerField(default=0, verbose_name=_("Points"))

    def __str__(self):
        return f"{self.player.user.username} - {self.date}"


class Forum(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, verbose_name=_("Player"))
    topic = models.CharField(max_length=300, verbose_name=_("Topic"))
    description = models.CharField(max_length=500, blank=True, verbose_name=_("Description"))
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))

    @staticmethod
    def get_not_deleted_forums():
        return list(Forum.objects.filter(is_deleted=False))

    def __str__(self):
        return self.topic


class Discussion(models.Model):
    """Child class of Forum that stores views from different users(players)"""
    
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, verbose_name=_("Forum"))
    discuss = models.CharField(max_length=500, verbose_name=_("Discussion"))

    def __str__(self):
        return self.forum.topic


class MultiPlayerSession(models.Model):
    room_code = models.CharField(max_length=100, primary_key=True, verbose_name=_("Room Code"))
    creator = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='creator', verbose_name=_("Creator"), null=True)
    players = models.ManyToManyField(Player, related_name='game_players', verbose_name=_("Players"))
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name=_("Quiz"))
    started = models.BooleanField(default=False, verbose_name=_("Started"))
    current_question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Current Question"))