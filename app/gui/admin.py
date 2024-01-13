from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from gui.models import Player


class PlayerInLine(admin.StackedInline):
    model = Player


class UserAdmin(BaseUserAdmin):
    inlines = [PlayerInLine]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)