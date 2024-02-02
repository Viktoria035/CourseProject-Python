from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres import fields

# Create your models here.
class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    level = models.CharField(max_length=200)

    def __str__(self):
        return self.user.username
    

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