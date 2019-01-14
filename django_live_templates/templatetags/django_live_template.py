# -*- coding: utf-8 -*-
from django.core.cache import InvalidCacheBackendError, caches
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.template import Context, Library
from django.db.models.query import QuerySet
from django.db.models import Model
import uuid

from ..utils import get_channel_cache, get_key_for_instance, get_key_for_queryset
from ..classes import ModelInstanceRef
from ..classes import ModelQuerySetRef
from ..classes import ContextRef

register = Library()

def listen_on_instance(channel_cache, cache_key, template_name, new_context, channel, instance_ref):
    chan_cache_key = 'djl.chan.%s' % channel    # This key stores: channel -> template via cache_key
    tmpl_cache_key = 'djl.tmpl.%s' % cache_key  # This key stores: template (name, context, channel)

    channel_cache.set(chan_cache_key, cache_key, timeout=300)
    channel_cache.set(tmpl_cache_key, (template_name, new_context, channel), timeout=300)

def listen_on_queryset(channel_cache, cache_key, template_name, new_context, channel, queryset_ref):
    chan_cache_key = 'djl.chan.%s' % channel    # This key stores: channel -> queryset via cache_key
    qset_cache_key = 'djl.qset.%s' % cache_key  # This key stores: queryset -> template
    tmpl_cache_key = 'djl.tmpl.%s' % cache_key  # This key stores: template (name, context, channel)

    channel_cache.set(chan_cache_key, cache_key, timeout=300)
    channel_cache.set(qset_cache_key, (queryset_ref, tmpl_cache_key), timeout=300)
    channel_cache.set(tmpl_cache_key, (template_name, new_context, channel), timeout=300)

@register.simple_tag(takes_context=True)
def include_live(context, template_name, **kwargs):
    if 'user' in context:
        user = context['user']
        kwargs['user'] = user
    else:
        user = None

    new_context_data = {}
    for key, value in kwargs.items():
        if isinstance(value, Model):
            new_context_data[key] = ModelInstanceRef.create(instance=value)
        elif isinstance(value, QuerySet):
            new_context_data[key] = ModelQuerySetRef.create(queryset=value)
        else:
            new_context_data[key] = value

    cache_keys = {}
    make_channel = lambda c: str(uuid.uuid5(uuid.NAMESPACE_DNS, c))
    for value in new_context_data.values():
        if isinstance(value, ModelInstanceRef):
            cache_key = get_key_for_instance(template_name, user,
                                             instance_ref=value)
            cache_keys[cache_key] = value, make_channel(cache_key)
        elif isinstance(value, ModelQuerySetRef):
            cache_key = get_key_for_queryset(template_name, user,
                                             queryset_ref=value)
            cache_keys[cache_key] = value, make_channel(cache_key)

    make_channel = lambda c: 'django-template-live-%s' % c[1]
    channels = map(make_channel, cache_keys.values())
    classes = 'django-template-live %s' % ' '.join(channels)

    new_context_data['django_live_template'] = classes
    new_context_data['is_django_live_template'] = False
    new_context = ContextRef(new_context_data)

    channel_cache = get_channel_cache()
    for cache_key, (value, channel) in cache_keys.items():
        if isinstance(value, ModelInstanceRef):
            listen_on_instance(channel_cache, cache_key, template_name,
                               new_context, channel, instance_ref=value)
        elif isinstance(value, ModelQuerySetRef):
            listen_on_queryset(channel_cache, cache_key, template_name,
                               new_context, channel, queryset_ref=value)

    return render_to_string(template_name, new_context.flatten())
