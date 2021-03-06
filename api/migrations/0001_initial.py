# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-08-28 16:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Event', '0001_initial'),
        ('Visitor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UhfTime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_id', models.CharField(blank=True, max_length=256, null=True)),
                ('direction', models.CharField(blank=True, max_length=2, null=True)),
                ('time_of_sec', models.DateTimeField(blank=True, null=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Event.Event')),
                ('lecture', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='Lecture_rel', to='Event.Lecture')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Visitor.EventProfile')),
            ],
        ),
    ]
