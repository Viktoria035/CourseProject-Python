from django.db import models
from django.contrib.auth.models import User

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


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice