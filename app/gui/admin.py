from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from gui.models import UserQ


class UserQInLine(admin.StackedInline):
    model = UserQ


class UserAdmin(BaseUserAdmin):
    inlines = [UserQInLine]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)