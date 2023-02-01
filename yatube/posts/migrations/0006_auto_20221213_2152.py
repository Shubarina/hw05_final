# Generated by Django 2.2.9 on 2022-12-13 16:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20221211_1336'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'ordering': (['title'],), 'verbose_name_plural': 'группы'},
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': (['-pub_date', 'author'],), 'verbose_name_plural': 'публикации'},
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='group', to='posts.Group'),
        ),
    ]
