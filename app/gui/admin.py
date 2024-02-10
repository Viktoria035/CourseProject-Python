from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from gui.models import Player, Result, Question, Quizz, Answer


class PlayerInLine(admin.StackedInline):
    model = Player


class UserAdmin(BaseUserAdmin):
    inlines = [PlayerInLine]


class AnswerInLine(admin.TabularInline):
    model = Answer


class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInLine]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)

admin.site.register(Quizz)
admin.site.register(Result)