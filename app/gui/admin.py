from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from gui.models import Player, Question, Quiz, Answer, Category, QuizAttempt, Forum, Discussion, PointsPerDay


class AnswerInLine(admin.TabularInline):
    model = Answer


class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInLine]

admin.site.register(Player)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)
admin.site.register(Quiz)
admin.site.register(Category)
admin.site.register(QuizAttempt)
admin.site.register(Forum)
admin.site.register(Discussion)
admin.site.register(PointsPerDay)
# admin.site.register(QuestionResponse)