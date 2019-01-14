# -*- coding: utf-8 -*-
from asgiref.sync import async_to_sync
from django.template.loader import render_to_string

def push_new_content_for_instance(channel_cache, instance_hash, instance_pk):
    cache_key_glob = 'djl.tmpl.i%s-t*' % instance_hash
    for tmpl_cache_key in channel_cache.iter_keys(cache_key_glob):
        yield lambda cl: push_new_content(cl, channel_cache, tmpl_cache_key)

def push_new_content_for_queryset(channel_cache, queryset_hash, queryset_pk):
    cache_key_glob = 'djl.qset.q%s-d*-t*' % queryset_hash
    for qset_cache_key in channel_cache.iter_keys(cache_key_glob):
        queryset_ref, tmpl_cache_key = channel_cache.get(qset_cache_key, (None, None))
        if queryset_ref and tmpl_cache_key:
            if queryset_ref.resolve().filter(pk=queryset_pk).exists():
                yield lambda cl: push_new_content(cl, channel_cache, tmpl_cache_key)

def push_new_content(channel_layer, channel_cache, cache_key):
    template_name, new_context, live_channel = channel_cache.get(cache_key, (None, None, None))
    if template_name and new_context and live_channel:
        new_context.update({'is_django_live_template': True})
        channel = 'django-template-live-%s' % live_channel
        content = render_to_string(template_name, new_context.flatten())
        event = {'type': 'publish', 'live_channel': channel, 'live_content': content}
        async_to_sync(channel_layer.group_send)(channel, event)
