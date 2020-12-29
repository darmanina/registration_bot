# Generated by Django 3.1.1 on 2020-12-29 15:08

import chattree.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chattree', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bot',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Бот включён/выключен'),
        ),
        migrations.AlterField(
            model_name='bot',
            name='token',
            field=models.CharField(help_text='<span style="color:red;font-weight:bold;">ВНИМАНИЕ: редактирование этого поля может сломать Вашего бота.</a>\n Получить токен для нового бота телеграм <br />можно с использованием <a href="https://t.me/BotFather">https://t.me/BotFather</a>', max_length=64, unique=True, validators=[chattree.models.validate_token], verbose_name='Токен'),
        ),
    ]
