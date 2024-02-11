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

class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    level = models.CharField(max_length=200)

    def __str__(self):
        return self.user.username
    

class CategoryManager(models.Manager):

    def new_category(self, name):
        category = self.create(category=re.sub('\s+', '-', category).lower())

        category.save()
        return category


class Category(models.Model):

    category = models.CharField(verbose_name=_("Category"), max_length=100, blank=True, unique=True, null=True)

    objects = CategoryManager()


    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.category
    
#not sure for this class what we are doing here ;()
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
    
    random_order = models.BooleanField(verbose_name=_("Random Order"), 
                                       blank=False, default=False, 
                                       help_text=_("Display the questions in a random order or as they are set?"))

    max_questions = models.PositiveIntegerField(verbose_name=_("Max Questions"), 
                                                blank=True, null=True, 
                                                help_text=_("Number of questions to be answered on each attempt"))

    answers_at_end = models.BooleanField(verbose_name=_("Answers at end"), 
                                         blank=False, default=False, 
                                         help_text=_("Display the correct answers when the quiz is finished?"))

    single_attempt = models.BooleanField(verbose_name=_("Single Attempt"), 
                                         blank=False, default=False, 
                                         help_text=_("If yes, only one attempt is permitted"))

    pass_mark = models.SmallIntegerField(verbose_name=_("Pass Mark"), 
                                         blank=True, default=0, 
                                         help_text=_("Percentage required to pass. Leave empty if no pass mark is required"), 
                                         validators=[MaxValueValidator(100)])

    success_text = models.TextField(verbose_name=_("Success Text"), 
                                    blank=True, 
                                    help_text=_("Displayed if user passes. HTML and Textile valid."))

    fail_text = models.TextField(verbose_name=_("Fail Text"), 
                                 blank=True, 
                                 help_text=_("Displayed if user fails. HTML and Textile valid."))

    draft = models.BooleanField(verbose_name=_("Draft"), 
                                blank=True, default=False, 
                                help_text=_("If yes, the quiz is not displayed in the quiz list and can only be taken by users who can edit quizzes."))


    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return f"{self.title} - {self.category} - {self.difficulty}"

    def get_questions(self):
        return self.question_set.all()[:self.max_questions] # we use the max_questions to limit the number of questions to be displayed
    
    @property
    def get_max_score(self):
        return self.get_questions().count()
    
    def anon_score_id(self):
        return str(self.id) + "_score"
    
    def anon_q_list(self):
        return str(self.id) + "_q_list"
    
    def anon_q_data(self):
        return str(self.id) + "_data"


class Question(models.Model):
    question = models.CharField(max_length=200)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    # max_marks = models.DecimalField(default=0, decimal_places=2, max_digits=6)
    # answer = models.CharField(max_length=200)

    def __str__(self):
        return self.question
    
    def get_answers(self):
        return self.answer_set.all() # we reverse reletionship to get all answers for a question, we can do this because we have a foreign key in the answer model


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    correct_answer = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"question: {self.question.question}, answer: {self.correct_answer}, is_correct: {self.is_correct}"


#     class Meta:
#         abstract = True

#     def __str__(self):
#         return self.correct_answer
    
#     def is_correct(self, user_answer):
#         return self.correct_answer == user_answer
    

class Result(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player.user.username} - {self.quiz.title} - {self.score}"

# #check
# class FreeTextAnswer(Answer):
#     case_sensitive = models.BooleanField(default=False)

#     def is_correct(self, user_answer):
#         if self.case_sensitive:
#             return self.correct_answer == user_answer
#         else:
#             return self.correct_answer.lower() == user_answer.lower()
        
# #check
# class MultipleChoiceAnswer(Answer):
#     choices = models.ManyToManyField(Answer, blank=True)

#     def __str__(self) -> str:
#         return f"{self.correct_answer} from {self.choices}"