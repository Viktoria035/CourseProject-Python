# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User

# class RegisterUserForm(UserCreationForm):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         for fieldname in ['username', 'password1', 'password2']:
#             self.fields[fieldname].help_text = None

#     class Meta:
#         model = User
#         fields = ("username", "email",
#                   "password1", "password2")

# If something is correct, the second one is -> UserRegisterForm and UserLogInForm

# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
# from django import forms

# class UserRegisterForm(UserCreationForm):
#     email=forms.EmailField()

#     class Meta:
#         model=User
#         fields=['username','email','password1','password2']

# class UserLogInForm(forms.ModelForm):
#     class Meta:
#         model=User
#         fields=['username','password']