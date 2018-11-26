# Generated by Django 2.1.3 on 2018-11-26 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20181126_1143'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
        migrations.RemoveField(
            model_name='user',
            name='team',
        ),
        migrations.AddField(
            model_name='user',
            name='team',
            field=models.ManyToManyField(to='app.Team'),
        ),
    ]
