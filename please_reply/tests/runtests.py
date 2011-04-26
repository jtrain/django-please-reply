#!/usr/bin/env python
import os
import sys

from django.conf import settings

this_dir = lambda name: os.path.join(os.path.dirname(__file__), name)

if not settings.configured:
    settings.configure(
      DATABASE_ENGINE='sqlite3',
      INSTALLED_APPS=[
          'django.contrib.contenttypes',
          'django.contrib.auth',
          'django.contrib.sessions',
          'django.contrib.admin',
          'django.contrib.messages',
          'please_reply',
          'please_reply.tests',
      ],
      #ROOT_URLCONF='please_reply.tests.urls',
      MEDIA_ROOT = this_dir('media'),
      TEMPLATE_CONTEXT_PROCESSORS =
                ('django.contrib.messages.context_processors.messages',
                 'django.core.context_processors.auth',),
      MIDDLEWARE_CLASSES =
                ('django.middleware.common.CommonMiddleware',
                 'django.contrib.sessions.middleware.SessionMiddleware',
                 'django.contrib.auth.middleware.AuthenticationMiddleware',
                 'django.contrib.messages.middleware.MessageMiddleware'),
      AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)
    )

from django.test.simple import run_tests


def runtests(*test_args):
    if not test_args:
        test_args = ['tests']
    parent = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
    )
    sys.path.insert(0, parent)
    failures = run_tests(test_args, verbosity=2, interactive=True)
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])
