from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserQ(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    score=models.IntegerField(default=0)
    position=models.IntegerField(default=0)
    title=models.CharField(max_length=200)

    def __str__(self):
        return self.username