# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-10 16:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spotify_playlists', '0002_auto_20160209_1945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='access_token',
            field=models.CharField(max_length=163),
        ),
        migrations.AlterField(
            model_name='user',
            name='refresh_token',
            field=models.CharField(max_length=131),
        ),
    ]
