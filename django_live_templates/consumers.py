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
    channel_names = []

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

    def publish(self, event):
        channel_name = event['channel_name']
        template_name = event['template_name']
        new_context = event['new_context']
        new_content = render_to_string(template_name, new_context.flatten())

        self.send(text_data=json.dumps({
            'live_channel': channel_name,
            'live_content': new_content
        }))


    def subscribe(self, channel_name):
        cache_key = self.validate_channel(channel_name)
        if cache_key:
            if not channel_name in self.channel_names:
                self.channel_names.append(channel_name)

                async_to_sync(self.channel_layer.group_add)(
                    channel_name,
                    self.channel_name
                )

            self.keep_channel_alive(channel_name, cache_key)

            self.send(text_data=json.dumps({
                'live_channel': channel_name,
            }))

    def unsubscribe(self, channel_name):
        cache_key = self.validate_channel(channel_name)
        if cache_key:
            if channel_name in self.channel_names:
                self.channel_names.remove(channel_name)

                async_to_sync(self.channel_layer.group_discard)(
                    channel_name,
                    self.channel_name
                )


    def validate_channel(self, channel_name):
        if channel_name.startswith('django-template-live-'):
            chan_cache_key = channel_name.replace('django-template-live-', 'djlt.chan.')
            cache_key = self.channel_cache.get(chan_cache_key, None)
            if not cache_key:
                return None

            cache_key_last_part = cache_key.split('-')[-1]
            if cache_key_last_part.startswith('u'):
                if self.user:
                    username_hash = get_username_hash(self.user)
                    if cache_key_last_part[1:] == username_hash:
                        return cache_key

            elif cache_key_last_part.startswith('t'):
                return cache_key

        return None

    def keep_channel_alive(self, channel_name, cache_key):
        chan_cache_key = channel_name.replace('django-template-live-', 'djlt.chan.')
        tmpl_cache_key = 'djlt.tmpl.%s' % cache_key
        qset_cache_key = 'djlt.qset.%s' % cache_key

        self.channel_cache.expire(chan_cache_key, timeout=300)
        self.channel_cache.expire(tmpl_cache_key, timeout=300)
        self.channel_cache.expire(qset_cache_key, timeout=300)
