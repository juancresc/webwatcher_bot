# Generated by Django 2.0.1 on 2018-01-21 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watcher', '0002_auto_20180121_1540'),
    ]

    operations = [
        migrations.AddField(
            model_name='website',
            name='name',
            field=models.TextField(default='a', verbose_name='name of the website'),
            preserve_default=False,
        ),
    ]