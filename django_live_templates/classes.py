#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
from django.template import Context

class ModelInstanceRef(object):
    __slots__ = 'instance_type_pk', 'instance_pk'

    @classmethod
    def create(cls, instance):
        instance_type = ContentType.objects.get_for_model(instance.__class__)
        return cls(instance_type.pk, instance.pk)

    def __init__(self, instance_type_pk, instance_pk):
        self.instance_type_pk = instance_type_pk
        self.instance_pk = instance_pk

    def resolve(self):
        instance_type = ContentType.objects.get_for_id(self.instance_type_pk)
        return instance_type.get_object_for_this_type(pk=self.instance_pk)

class ModelQuerySetRef(object):
    __slots__ = 'queryset_type_pk', 'query'

    @classmethod
    def create(cls, queryset):
        queryset_type = ContentType.objects.get_for_model(queryset.model)
        return cls(queryset_type.pk, queryset.query)

    def __init__(self, queryset_type_pk, query):
        self.queryset_type_pk = queryset_type_pk
        self.query = query

    def resolve(self):
        instance_type = ContentType.objects.get_for_id(self.queryset_type_pk)
        return QuerySet(model=instance_type.model_class(), query=self.query)

class ContextRef(Context):
    def __getitem__(self, key):
        item = super().__getitem__(key)
        return self._resolve_ref(item)

    def get(self, key, otherwise=None):
        item = super().get(key, otherwise)
        return self._resolve_ref(item)

    def flatten(self):
        data = super().flatten()
        return dict(map(lambda i: (i[0], self._resolve_ref(i[1])), data.items()))

    def _resolve_ref(self, item):
        if isinstance(item, ModelInstanceRef) or isinstance(item, ModelQuerySetRef):
            return item.resolve()
        else:
            return item
