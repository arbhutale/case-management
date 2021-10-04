# Generated by Django 3.2.4 on 2021-10-01 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case_management', '0008_caseoffice_case_office_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='legalcase',
            name='state',
            field=models.CharField(choices=[('Opened', 'Opened'), ('InProgress', 'In Progress'), ('Hanging', 'Hanging'), ('Pending', 'Pending'), ('Referred', 'Referred'), ('Resolved', 'Resolved'), ('Escalated', 'Escalated'), ('Closed', 'Closed')], max_length=10),
        ),
    ]
