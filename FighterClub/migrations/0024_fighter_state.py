# Generated by Django 5.1.6 on 2025-03-17 07:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FighterClub', '0023_auto_20250317_1011'),
    ]

    operations = [
        migrations.AddField(
            model_name='fighter',
            name='state',
            field=models.ForeignKey(default='Инвентарь', on_delete=django.db.models.deletion.CASCADE, to='FighterClub.fighterstate'),
        ),
    ]
