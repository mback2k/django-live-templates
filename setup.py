# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

def read_file(filename):
    """Read a file into a string"""
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except IOError:
        return ''

setup(
    name='django-live-templates',
    version=__import__('django_live_templates').__version__,
    author='Marc Hoersken',
    author_email='info@marc-hoersken.de',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/mback2k/django-live-templates',
    license='MIT',
    description=u' '.join(__import__('django_live_templates').__doc__.splitlines()).strip(),
    install_requires=['channels', 'django-redis'],
    classifiers=[
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
    ],
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
)
