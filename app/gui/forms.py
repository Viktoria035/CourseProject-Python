from django import forms
from .models import Player, Category, Quiz, Question, Answer, Forum, Discussion

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__" # ['category']


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = "__all__" # ['title', 'description', 'difficulty', 'category', 'max_questions', 'pass_mark']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = "__all__" # ['question', 'quiz', 'question_type']


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = "__all__" # ['question', 'answer', 'points', 'is_correct']


class CreateInForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = "__all__"


class CreateInDiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = "__all__"