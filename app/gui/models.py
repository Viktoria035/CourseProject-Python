from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from django.core.validators import MaxValueValidator
import re
# Create your models here.

DIFF_CHOICES = (
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
)

QUESTION_TYPES = (
    ('single choice', 'Single Choice'),
    ('multiple choice', 'Multiple Choice'),
    #('true or false', 'True or False'),
)

class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    level = models.CharField(max_length=200, default='Beginner')
    active_attempt = models.ForeignKey('QuizAttempt', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.user.username


class Category(models.Model):

    category = models.CharField(verbose_name=_("Category"), max_length=100, unique=True, null=True)
    player = models.ForeignKey(Player, verbose_name=_("Player"), on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.category
    

class Quiz(models.Model):

    title = models.CharField(verbose_name=_("Title"), 
                             max_length=100, blank=False)

    description = models.TextField(verbose_name=_("Description"), 
                                   blank=True,
                                     help_text=_("A brief description of the quiz"))

    difficulty = models.CharField(verbose_name=_("Difficulty"), 
                                  max_length=6, 
                                  choices=DIFF_CHOICES, default='easy')

    category = models.ForeignKey(Category, null=True, 
                                 blank=True, verbose_name=_("Category"), 
                                 on_delete=models.CASCADE)
    
    player = models.ForeignKey(Player, verbose_name=_("Player"),
                               help_text=_("The player who created the quiz."),
                               on_delete=models.CASCADE, null=True)

    # random_order = models.BooleanField(verbose_name=_("Random Order"), 
    #                                    blank=False, default=False, 
    #                                    help_text=_("Display the questions in a random order or as they are set?"))

    max_questions = models.PositiveIntegerField(verbose_name=_("Max Questions"), 
                                                blank=True, null=True, 
                                                help_text=_("Number of questions to be answered on each attempt"))

    # answers_at_end = models.BooleanField(verbose_name=_("Answers at end"), 
    #                                      blank=False, default=False, 
    #                                      help_text=_("Display the correct answers when the quiz is finished?"))

    # single_attempt = models.BooleanField(verbose_name=_("Single Attempt"), 
    #                                      blank=False, default=False, 
    #                                      help_text=_("If yes, only one attempt is permitted"))

    pass_mark = models.SmallIntegerField(verbose_name=_("Pass Mark"), 
                                         blank=True, default=0, 
                                         help_text=_("Percentage required to pass. Leave empty if no pass mark is required"), 
                                         validators=[MaxValueValidator(100)])

    # success_text = models.TextField(verbose_name=_("Success Text"), 
    #                                 blank=True, 
    #                                 help_text=_("Displayed if user passes. HTML and Textile valid."))

    # fail_text = models.TextField(verbose_name=_("Fail Text"), 
    #                              blank=True, 
    #                              help_text=_("Displayed if user fails. HTML and Textile valid."))

    # draft = models.BooleanField(verbose_name=_("Draft"), 
    #                             blank=True, default=False, 
    #                             help_text=_("If yes, the quiz is not displayed in the quiz list and can only be taken by users who can edit quizzes."))


    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return f"{self.title} - {self.category} - {self.difficulty}"

    def get_questions(self):
        return self.question_set.all()[:self.max_questions] # we use the max_questions to limit the number of questions to be displayed


class Question(models.Model):
    question = models.CharField(max_length=200)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    question_type = models.CharField(max_length=15, choices=QUESTION_TYPES, default='single choice')
    # player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.question
    
    # def get_answers(self):
    #     return self.answer_set.all() # we reverse reletionship to get all answers for a question, we can do this because we have a foreign key in the answer model


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    points = models.IntegerField(default=1)
    is_correct = models.BooleanField(default=False)
    # player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.answer} - {self.points}"
    

class QuestionResponse(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    
    def is_correct(self):
        return self.answer.is_correct

    def __str__(self):
        return self.answer


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)
    responses = models.ManyToManyField(QuestionResponse)

    def __str__(self):
        return f"{self.player.user.username} - {self.quiz.title}"
    

class Forum(models.Model):
    player_name = models.CharField(max_length=200, default='Anonymous')
    topic = models.CharField(max_length=300)
    description = models.CharField(max_length=500, blank=True)
    #link = models.CharField(max_length=200, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.topic


class Discussion(models.Model):
    """Child class of Forum that stores views from different users(players)"""
    
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    discuss = models.CharField(max_length=500)

    def __str__(self):
        return self.forum.topic