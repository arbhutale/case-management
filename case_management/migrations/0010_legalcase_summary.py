# Generated by Django 3.2.4 on 2021-10-01 14:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case_management', '0009_auto_20211001_1328'),
    ]

    operations = [
        migrations.AddField(
            model_name='legalcase',
            name='summary',
            field=models.TextField(blank=True, default=''),
        ),
    ]
