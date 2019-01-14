from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json

from .utils import get_channel_cache, get_username_hash

class LiveTemplatesConsumer(WebsocketConsumer):
    live_channels = []

    def connect(self):
        self.user = self.scope["user"]
        self.channel_cache = get_channel_cache()
        self.accept()

    def disconnect(self, close_code):
        for live_channel in self.live_channels:
            self.unsubscribe(live_channel)

    def receive(self, text_data):
        live_channel = text_data

        self.subscribe(live_channel)

    def publish(self, event):
        live_channel = event['live_channel']
        live_content = event['live_content']

        self.send(text_data=json.dumps({
            'live_channel': live_channel,
            'live_content': live_content
        }))


    def subscribe(self, live_channel):
        cache_key = self.validate_channel(live_channel)
        if cache_key:
            if not live_channel in self.live_channels:
                self.live_channels.append(live_channel)

                async_to_sync(self.channel_layer.group_add)(
                    live_channel,
                    self.channel_name
                )

            self.keep_channel_alive(live_channel, cache_key)

            self.send(text_data=json.dumps({
                'live_channel': live_channel,
            }))

    def unsubscribe(self, live_channel):
        cache_key = self.validate_channel(live_channel)
        if cache_key:
            if live_channel in self.live_channels:
                self.live_channels.remove(live_channel)

                async_to_sync(self.channel_layer.group_discard)(
                    live_channel,
                    self.channel_name
                )


    def validate_channel(self, live_channel):
        if live_channel.startswith('django-template-live-'):
            chan_cache_key = live_channel.replace('django-template-live-', 'djl.chan.')
            cache_key = self.channel_cache.get(chan_cache_key, None)
            if not cache_key:
                return None

            cache_key_last_part = cache_key.split('-')[-1]
            if cache_key_last_part.startswith('u'):
                if self.user:
                    username_hash = get_username_hash(self.user)
                    if cache_key_last_part[1:] == username_hash:
                        return cache_key

            elif cache_key_last_part.startswith('f'):
                return cache_key

        return None

    def keep_channel_alive(self, live_channel, cache_key):
        chan_cache_key = live_channel.replace('django-template-live-', 'djl.chan.')
        tmpl_cache_key = 'djl.tmpl.%s' % cache_key
        qset_cache_key = 'djl.qset.%s' % cache_key

        self.channel_cache.expire(chan_cache_key, timeout=300)
        self.channel_cache.expire(tmpl_cache_key, timeout=300)
        self.channel_cache.expire(qset_cache_key, timeout=300)
