# Generated by Django 5.1.6 on 2025-02-24 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FighterClub', '0005_alter_armor_body_part'),
    ]

    operations = [
        migrations.CreateModel(
            name='Treasure',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('price', models.IntegerField(default=0)),
                ('sell_coeff', models.DecimalField(decimal_places=2, default=1, max_digits=5)),
            ],
        ),
        migrations.AddField(
            model_name='armor',
            name='price',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='armor',
            name='sell_coeff',
            field=models.DecimalField(decimal_places=2, default=0.5, max_digits=5),
        ),
        migrations.AddField(
            model_name='weapon',
            name='price',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='weapon',
            name='sell_coeff',
            field=models.DecimalField(decimal_places=2, default=0.5, max_digits=5),
        ),
    ]
