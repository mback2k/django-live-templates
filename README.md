[Django-Live-Templates](https://github.com/mback2k/django-live-templates) is
an extension to [Django](https://www.djangoproject.com/) and
[Channels](https://channels.readthedocs.io/) which adds
support for live updating Django template snippets on model changes.

This project is based upon and a partial reimplementation to Channels of
[SwampDragon-live](https://github.com/mback2k/swampdragon-live) which was build
using [SwampDragon](https://github.com/hagsteel/swampdragon)
with SwampDragon-auth and django-redis.

Installation
------------
Install the latest version from pypi.python.org:

    pip install django-live-templates

Install the development version by cloning the source from github.com:

    pip install git+https://github.com/mback2k/django-live-templates.git

Configuration
-------------
Add the package to your `INSTALLED_APPS`:

    INSTALLED_APPS += (
        'channels',
        'django_live_templates',
    )

Example
-------
Make sure to use django-redis as a Cache backend named 'django-live-templates' or 'default':

    CACHES = {
        'django-live-templates': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://localhost:6379/0',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }

Load the required JavaScript template-tags within your Django template:

    {% load django_live_template %}

Add the required JavaScript to your Django template:

    <script type="text/javascript" src="{{ STATIC_URL }}js/django_live_template.js"></script>

Use the include_live template-tag instead of the default include template-tag,
with rows being a Django database QuerySet to listen for added, changed, deleted instances:

    {% include_live 'includes/table_body.html' rows=rows perms=perms %}

Use the include_live template-tag instead of the default include template-tag,
with row being a single Django database Model instance to listen for changes:

    {% include_live 'includes/row_cols.html' row=row perms=perms %}

Use the django_live_template variable within the included template to add the
required classes to the root-tag of this template, e.g. the first tag-node:

    <tr class="{{ django_live_template }}">...</tr>

You can check if your template is being live rendered by a content pusher by
using the context variable `is_django_live_template` like this:

    {% if is_django_live_template %}
    <style onload="alert('Hello World!');"></style>
    {% endif %}

A real-world example can be found in the Django project WebGCal:
* https://github.com/mback2k/django-webgcal/blob/master/webgcal/apps/webgcal/templates/show_dashboard.html
* https://github.com/mback2k/django-webgcal/tree/master/webgcal/apps/webgcal/templates/includes

License
-------
* Released under MIT License
* Copyright (c) 2015-2019 Marc Hoersken <info@marc-hoersken.de>
