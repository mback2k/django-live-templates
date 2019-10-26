#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.template.loader import render_to_string
import json

from .utils import get_channel_cache, get_username_hash

class LiveTemplatesConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.user = None
        self.channel_cache = None
        self.channel_names = []
        super().__init__(*args, **kwargs)

    def connect(self):
        self.user = self.scope["user"]
        self.channel_cache = get_channel_cache()
        self.accept()

    def disconnect(self, close_code):
        for channel_name in self.channel_names:
            self.unsubscribe(channel_name)

    def receive(self, text_data):
        channel_name = text_data
        self.subscribe(channel_name)


    def instance_change(self, event):
        instance_hash = event['hash']

        cache_key_glob = 'djlt.tmpl.i%s-t*' % instance_hash
        for tmpl_cache_key in self.channel_cache.iter_keys(cache_key_glob):
            self.push_new_content(tmpl_cache_key)

    def queryset_change(self, event):
        queryset_hash = event['hash']
        queryset_pk = event['pk']

        cache_key_glob = 'djlt.qset.q%s-d*-t*' % queryset_hash
        for qset_cache_key in self.channel_cache.iter_keys(cache_key_glob):
            queryset_ref, tmpl_cache_key, channel_name = self.channel_cache.get(qset_cache_key, (None, None, None))
            if queryset_ref and tmpl_cache_key and channel_name in self.channel_names:
                # TODO: fix handling of deletion for queryset changes
                if queryset_ref.resolve().filter(pk=queryset_pk).exists():
                    self.push_new_content(tmpl_cache_key)


    def push_new_content(self, tmpl_cache_key):
        template_name, new_context, channel_name = self.channel_cache.get(tmpl_cache_key, (None, None, None))
        if template_name and new_context and channel_name in self.channel_names:
            new_context['is_django_live_template'] = True
            new_content = render_to_string(template_name, new_context.flatten())

            self.send(text_data=json.dumps({
                'live_channel': channel_name,
                'live_content': new_content
            }))


    def subscribe(self, channel_name):
        cache_key, channel_hash = self.validate_channel(channel_name)
        if cache_key and channel_hash:
            if not channel_name in self.channel_names:
                self.channel_names.append(channel_name)

                async_to_sync(self.channel_layer.group_add)(
                    channel_hash,
                    self.channel_name
                )

            self.keep_channel_alive(channel_name, cache_key)

            self.send(text_data=json.dumps({
                'live_channel': channel_name,
            }))

    def unsubscribe(self, channel_name):
        cache_key, channel_hash = self.validate_channel(channel_name)
        if cache_key and channel_hash:
            if channel_name in self.channel_names:
                self.channel_names.remove(channel_name)

                async_to_sync(self.channel_layer.group_discard)(
                    channel_hash,
                    self.channel_name
                )


    def validate_channel(self, channel_name):
        if channel_name.startswith('django-template-live-'):
            # TODO: rework handling of channel_uuid and cache_key
            chan_cache_key = channel_name.replace('django-template-live-', 'djlt.chan.')
            cache_key, channel_hash = self.channel_cache.get(chan_cache_key, (None, None))
            if not cache_key or not channel_hash:
                return None, None

            cache_key_last_part = cache_key.split('-')[-1]
            if cache_key_last_part.startswith('u'):
                if self.user:
                    username_hash = get_username_hash(self.user.username)
                    if cache_key_last_part[1:] == username_hash:
                        return cache_key, channel_hash

            elif cache_key_last_part.startswith('t'):
                return cache_key, channel_hash

        return None, None

    def keep_channel_alive(self, channel_name, cache_key):
        chan_cache_key = channel_name.replace('django-template-live-', 'djlt.chan.')
        tmpl_cache_key = 'djlt.tmpl.%s' % cache_key
        qset_cache_key = 'djlt.qset.%s' % cache_key

        self.channel_cache.expire(chan_cache_key, timeout=300)
        self.channel_cache.expire(tmpl_cache_key, timeout=300)
        self.channel_cache.expire(qset_cache_key, timeout=300)
