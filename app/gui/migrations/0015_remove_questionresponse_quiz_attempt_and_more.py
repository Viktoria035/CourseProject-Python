# Generated by Django 4.2.9 on 2024-02-12 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gui', '0014_questionresponse_quiz_attempt'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='questionresponse',
            name='quiz_attempt',
        ),
        migrations.RemoveField(
            model_name='quizattempt',
            name='attempt',
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='responses',
            field=models.ManyToManyField(to='gui.questionresponse'),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='score',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='Attempt',
        ),
    ]
