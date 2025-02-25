# Generated by Django 5.1.6 on 2025-02-25 10:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('FighterClub', '0008_alter_fighter_weapon'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fighterequipment',
            old_name='body_part_name',
            new_name='body_part',
        ),
        migrations.RenameField(
            model_name='fighterequipment',
            old_name='fighter_id',
            new_name='fighter',
        ),
        migrations.AlterUniqueTogether(
            name='fighterequipment',
            unique_together={('fighter', 'body_part')},
        ),
    ]
