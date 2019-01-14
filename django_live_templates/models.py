# -*- coding: utf-8 -*-
from channels.layers import get_channel_layer
from django.db.models.signals import post_save, pre_delete, post_delete
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver

from .utils import get_channel_cache, get_instance_hash, get_queryset_hash
from .pushers import push_new_content_for_instance
from .pushers import push_new_content_for_queryset

@receiver(post_save)
def post_save_handler(sender, instance, created, **kwargs):
    if ContentType.objects.exists():
        instance_type = ContentType.objects.get_for_model(instance.__class__)
        channel_cache = get_channel_cache()
        channel_layer = get_channel_layer()

        if created:
            queryset_hash = get_queryset_hash(instance_type.pk)
            pushers = push_new_content_for_queryset(channel_cache, queryset_hash, instance.pk)
        else:
            instance_hash = get_instance_hash(instance_type.pk, instance.pk)
            pushers = push_new_content_for_instance(channel_cache, instance_hash, instance.pk)

        for pusher in pushers:
            pusher(channel_layer)

@receiver(pre_delete)
def pre_delete_handler(sender, instance, **kwargs):
    if ContentType.objects.exists():
        instance_type = ContentType.objects.get_for_model(instance.__class__)
        channel_cache = get_channel_cache()

        queryset_hash = get_queryset_hash(instance_type.pk)
        pushers = push_new_content_for_queryset(channel_cache, queryset_hash, instance.pk)
        instance.__django_live_template_pushers__ = list(pushers)

@receiver(post_delete)
def post_delete_handler(sender, instance, **kwargs):
    if hasattr(instance, '__django_live_template_pushers__'):
        channel_layer = get_channel_layer()

        for pusher in instance.__django_live_template_pushers__:
            pusher(channel_layer)
