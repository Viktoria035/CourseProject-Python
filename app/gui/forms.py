from django import forms
from .models import Player, Category, Quiz, Question, Answer, Forum, Discussion

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category']


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'difficulty', 'category', 'max_questions', 'pass_mark']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question', 'quiz', 'question_type']


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['question', 'answer', 'points', 'is_correct']


class CreateInForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ['topic', 'description']


class CreateInDiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ['forum', 'discuss']