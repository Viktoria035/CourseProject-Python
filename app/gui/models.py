from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres import fields
from django.utils.translation import ugettext as _
from django.core.validators import MaxValueValidator

# Create your models here.
class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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

    category = models.CharField(verbose_name=_("Category"), max_length=250, blank=True, unique=True, null=True)

    objects = CategoryManager()


    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.category
    

class Quizz(models.Model):

    title = models.CharField(verbose_name=_("Title"), max_length=100, blank=False)

    description = models.TextField(verbose_name=_("Description"), blank=True, help_text=_("A brief description of the quiz"))

    url = models.SlugField(verbose_name=_("user friendly url"), max_length=60, blank=False, help_text=_("A user friendly url"))

    category = models.ForeignKey(Category, null=True, blank=True, verbose_name=_("Category"), on_delete=models.CASCADE)
    
    random_order = models.BooleanField(verbose_name=_("Random Order"), blank=False, default=False, help_text=_("Display the questions in a random order or as they are set?"))

    max_questions = models.PositiveIntegerField(verbose_name=_("Max Questions"), blank=True, null=True, help_text=_("Number of questions to be answered on each attempt"))

    answers_at_end = models.BooleanField(verbose_name=_("Answers at end"), blank=False, default=False, help_text=_("Display the correct answers when the quiz is finished?"))

    exam_paper = models.BooleanField(verbose_name=_("Exam Paper"), blank=False, default=False, help_text=_("If yes, the quiz is presented in exam mode - no correct answers until the end"))

    single_attempt = models.BooleanField(verbose_name=_("Single Attempt"), blank=False, default=False, help_text=_("If yes, only one attempt is permitted"))

    pass_mark = models.SmallIntegerField(verbose_name=_("Pass Mark"), blank=True, default=0, help_text=_("Percentage required to pass. Leave empty if no pass mark is required"), validators=[MaxValueValidator(100)])

    success_text = models.TextField(verbose_name=_("Success Text"), blank=True, help_text=_("Displayed if user passes. HTML and Textile valid."))

    fail_text = models.TextField(verbose_name=_("Fail Text"), blank=True, help_text=_("Displayed if user fails. HTML and Textile valid."))

    draft = models.BooleanField(verbose_name=_("Draft"), blank=True, default=False, help_text=_("If yes, the quiz is not displayed in the quiz list and can only be taken by users who can edit quizzes."))

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.url = re.sub('\s+', '-', self.url).lower()

        self.url = ''.join(letter for letter in self.url if letter.isalnum() or letter == '-')

        if self.single_attempt is True:
            self.exam_paper = True

        if self.pass_mark > 100:
            raise ValueError("Pass mark cannot be greater than 100")
        
        super(Quizz, self).save(force_insert, force_update, *args, **kwargs)
    
    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.question_set.all().select_subclasses()
    
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
    question = models.CharField(max_length=500)
    max_marks=models.DecimalField(default=0,decimal_places=2,max_digits=6)
    category = models.CharField(max_length=200)
    #answer = models.CharField(max_length=200)

    def __str__(self):
        return self.question


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    correct_answer = models.CharField(max_length=500)
    #is_correct = models.BooleanField(default=False)


    class Meta:
        abstract = True

    def __str__(self):
        return self.correct_answer
    
    def is_correct(self, user_answer):
        return self.correct_answer == user_answer
    
#check
class FreeTextAnswer(Answer):
    case_sensitive = models.BooleanField(default=False)

    def is_correct(self, user_answer):
        if self.case_sensitive:
            return self.correct_answer == user_answer
        else:
            return self.correct_answer.lower() == user_answer.lower()
        
#check
class MultipleChoiceAnswer(Answer):
    choices = fields.ArrayField(models.CharField(max_length=200, blank=True))

    def __str__(self) -> str:
        return f"{self.correct_answer} from {self.choices}"