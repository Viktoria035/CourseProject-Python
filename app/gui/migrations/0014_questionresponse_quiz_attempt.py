# Generated by Django 4.2.9 on 2024-02-12 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gui', '0013_attempt_delete_result_quizattempt_attempt'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionresponse',
            name='quiz_attempt',
            field=models.ManyToManyField(to='gui.quizattempt'),
        ),
    ]
