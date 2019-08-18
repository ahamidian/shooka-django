# Generated by Django 2.1.3 on 2019-02-06 12:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_auto_20190102_0929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='singlecriteria',
            name='criteria_clause',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='singles', to='app.CriteriaClause'),
        ),
        migrations.AlterField(
            model_name='singlecriteria',
            name='value_type',
            field=models.CharField(default='string', max_length=255),
        ),
    ]