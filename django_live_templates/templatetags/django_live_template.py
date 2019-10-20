#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.cache import InvalidCacheBackendError, caches
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.template import Context, Library
from django.db.models.query import QuerySet
from django.db.models import Model

from ..utils import get_channel_cache, get_channel_uuid, get_key_for_instance, get_key_for_queryset
from ..classes import ModelInstanceRef
from ..classes import ModelQuerySetRef
from ..classes import ContextRef

register = Library()

def listen_on_instance(channel_cache, cache_key, template_name, new_context, channel_uuid, instance_ref):
    chan_cache_key = 'djlt.chan.%s' % channel_uuid # This key stores: channel_uuid -> template via cache_key
    tmpl_cache_key = 'djlt.tmpl.%s' % cache_key    # This key stores: template (name, context, channel_uuid)

    channel_cache.set(chan_cache_key, cache_key, timeout=300)
    channel_cache.set(tmpl_cache_key, (template_name, new_context, channel_uuid), timeout=300)

def listen_on_queryset(channel_cache, cache_key, template_name, new_context, channel_uuid, queryset_ref):
    chan_cache_key = 'djlt.chan.%s' % channel_uuid # This key stores: channel_uuid -> queryset via cache_key
    qset_cache_key = 'djlt.qset.%s' % cache_key    # This key stores: queryset -> template
    tmpl_cache_key = 'djlt.tmpl.%s' % cache_key    # This key stores: template (name, context, channel_uuid)

    channel_cache.set(chan_cache_key, cache_key, timeout=300)
    channel_cache.set(qset_cache_key, (queryset_ref, tmpl_cache_key), timeout=300)
    channel_cache.set(tmpl_cache_key, (template_name, new_context, channel_uuid), timeout=300)

@register.simple_tag(takes_context=True)
def include_live(context, template_name, **kwargs):
    if 'user' in context:
        user = context['user']
        kwargs['user'] = user
    else:
        user = None

    cache_keys = {}
    new_context_data = {}
    css_classes = 'django-template-live'
    for key, value in kwargs.items():
        if isinstance(value, Model):
            value = ModelInstanceRef.create(instance=value)
            cache_key = get_key_for_instance(template_name, user,
                                             instance_ref=value)
            channel_uuid = get_channel_uuid(cache_key)
            css_classes = '%s django-template-live-%s' % (css_classes, channel_uuid)
            cache_keys[cache_key] = value, channel_uuid
        elif isinstance(value, QuerySet):
            value = ModelQuerySetRef.create(queryset=value)
            cache_key = get_key_for_queryset(template_name, user,
                                             queryset_ref=value)
            channel_uuid = get_channel_uuid(cache_key)
            css_classes = '%s django-template-live-%s' % (css_classes, channel_uuid)
            cache_keys[cache_key] = value, channel_uuid
        new_context_data[key] = value

    new_context_data['django_live_template'] = css_classes
    new_context_data['is_django_live_template'] = False
    new_context = ContextRef(new_context_data)

    channel_cache = get_channel_cache()
    for cache_key, (value, channel_uuid) in cache_keys.items():
        if isinstance(value, ModelInstanceRef):
            listen_on_instance(channel_cache, cache_key, template_name,
                               new_context, channel_uuid, instance_ref=value)
        elif isinstance(value, ModelQuerySetRef):
            listen_on_queryset(channel_cache, cache_key, template_name,
                               new_context, channel_uuid, queryset_ref=value)

    return render_to_string(template_name, new_context.flatten())
