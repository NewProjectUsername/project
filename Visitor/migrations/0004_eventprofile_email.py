# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-10-03 06:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Visitor', '0003_auto_20170922_1106'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventprofile',
            name='email',
            field=models.EmailField(blank=True, max_length=256, null=True),
        ),
    ]
