#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^ws/live/templates/$', consumers.LiveTemplatesConsumer),
]
