# -*- coding: utf-8 -*-
from django.core.cache import InvalidCacheBackendError, caches
import hashlib

def get_channel_cache():
    try:
        channel_cache = caches['django-live-templates']
    except InvalidCacheBackendError:
        channel_cache = caches['default']
    return channel_cache

def get_instance_hash(instance_type_pk, instance_pk):
    instance_hash = hashlib.sha1(str('%d:%d' % (instance_type_pk, instance_pk)).encode('utf-8'))
    return instance_hash.hexdigest()

def get_queryset_hash(queryset_type_pk):
    queryset_hash = hashlib.sha1(str('%d:qs' % queryset_type_pk).encode('utf-8'))
    return queryset_hash.hexdigest()

def get_template_hash(template_name):
    template_hash = hashlib.sha1(template_name.encode('utf-8'))
    return template_hash.hexdigest()

def get_username_hash(user):
    username_hash = hashlib.sha1(user.username.encode('utf-8'))
    return username_hash.hexdigest()

def get_key_for_instance(template_name, user, instance_ref):
    instance_type_pk = instance_ref.instance_type_pk
    instance_pk = instance_ref.instance_pk

    instance_hash = get_instance_hash(instance_type_pk, instance_pk)
    template_hash = get_template_hash(template_name)
    cache_key = 'i%s-t%s' % (instance_hash, template_hash)

    if user:
        username_hash = get_username_hash(user)
        cache_key = '%s-u%s' % (cache_key, username_hash)

    return cache_key

def get_key_for_queryset(template_name, user, queryset_ref):
    queryset_type_pk = queryset_ref.queryset_type_pk
    queryset_dump = hashlib.sha1(str(queryset_ref.query).encode('utf-8')).hexdigest()

    queryset_hash = get_queryset_hash(queryset_type_pk)
    template_hash = get_template_hash(template_name)
    cache_key = 'q%s-d%s-t%s' % (queryset_hash, queryset_dump, template_hash)

    if user:
        username_hash = get_username_hash(user)
        cache_key = '%s-u%s' % (cache_key, username_hash)

    return cache_key
