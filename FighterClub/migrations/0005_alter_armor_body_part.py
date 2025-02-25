# Generated by Django 5.1.6 on 2025-02-24 10:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FighterClub', '0004_armor_body_part'),
    ]

    operations = [
        migrations.AlterField(
            model_name='armor',
            name='body_part',
            field=models.ForeignKey(default='Голова', on_delete=django.db.models.deletion.CASCADE, to='FighterClub.bodypart'),
            preserve_default=False,
        ),
    ]
