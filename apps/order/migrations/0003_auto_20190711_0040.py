# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-07-10 16:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0002_auto_20190621_0150'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordergoods',
            name='comment',
            field=models.CharField(default='', max_length=256, verbose_name='评论'),
        ),
    ]
