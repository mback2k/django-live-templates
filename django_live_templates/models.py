#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, post_delete
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver

from .utils import get_channel_cache, get_instance_hash, get_queryset_hash

@receiver(post_save)
def post_save_handler(sender, instance, created, **kwargs):
    if ContentType.objects.exists():
        instance_type = ContentType.objects.get_for_model(instance.__class__)
        channel_layer = get_channel_layer()

        if created:
            channel_hash = get_queryset_hash(instance_type.pk)
            channel_type = 'queryset.change'
        else:
            channel_hash = get_instance_hash(instance_type.pk, instance.pk)
            channel_type = 'instance.change'

        event = {'hash': channel_hash, 'type': channel_type,
                 'type_pk': instance_type.pk, 'pk': instance.pk}
        async_to_sync(channel_layer.group_send)(channel_hash, event)

@receiver(post_delete)
def post_delete_handler(sender, instance, **kwargs):
    if ContentType.objects.exists():
        instance_type = ContentType.objects.get_for_model(instance.__class__)
        channel_layer = get_channel_layer()

        channel_hash = get_queryset_hash(instance_type.pk)
        channel_type = 'queryset.change'

        event = {'hash': channel_hash, 'type': channel_type,
                 'type_pk': instance_type.pk, 'pk': instance.pk}
        async_to_sync(channel_layer.group_send)(channel_hash, event)
