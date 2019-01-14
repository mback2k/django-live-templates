from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^ws/live/templates/$', consumers.LiveTemplatesConsumer),
]
