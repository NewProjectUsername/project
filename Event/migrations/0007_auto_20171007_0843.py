# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-10-07 06:43
from __future__ import unicode_literals

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('Event', '0006_paymentticket_free'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='participant_fields',
            field=jsonfield.fields.JSONField(blank=True, default=['name', 'surname'], null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='participant_reqired_fields',
            field=jsonfield.fields.JSONField(blank=True, default=['name', 'surname'], null=True),
        ),
    ]
