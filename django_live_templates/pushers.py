#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from asgiref.sync import async_to_sync

from .utils import get_instance_hash, get_queryset_hash

def push_new_content_for_instance(channel_cache, instance_type_pk, instance_pk):
    instance_hash = get_instance_hash(instance_type_pk, instance_pk)
    cache_key_glob = 'djlt.tmpl.i%s-t*' % instance_hash
    for tmpl_cache_key in channel_cache.iter_keys(cache_key_glob):
        yield lambda cl: push_new_content(cl, channel_cache, tmpl_cache_key)

def push_new_content_for_queryset(channel_cache, queryset_type_pk, queryset_pk):
    queryset_hash = get_queryset_hash(queryset_type_pk)
    cache_key_glob = 'djlt.qset.q%s-d*-t*' % queryset_hash
    for qset_cache_key in channel_cache.iter_keys(cache_key_glob):
        queryset_ref, tmpl_cache_key = channel_cache.get(qset_cache_key, (None, None))
        if queryset_ref and tmpl_cache_key:
            if queryset_ref.resolve().filter(pk=queryset_pk).exists():
                yield lambda cl: push_new_content(cl, channel_cache, tmpl_cache_key)

def push_new_content(channel_layer, channel_cache, cache_key):
    template_name, new_context, channel_uuid = channel_cache.get(cache_key, (None, None, None))
    if template_name and new_context and channel_uuid:
        new_context.update({'is_django_live_template': True})
        channel_name = 'django-template-live-%s' % channel_uuid
        event = {'type': 'publish', 'channel_name': channel_name,
                 'template_name': template_name, 'new_context': new_context}
        async_to_sync(channel_layer.group_send)(channel_name, event)
