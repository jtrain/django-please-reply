django-please-reply
===================

Ever had to track who had and had not replied to an event? Who hasn't right?
We all have, and implementing this simple feature every time is time consuming.

This app will track who has and hasn't replied to an event from any event
framework. If you want to track recurring events, you need to look elsewhere
because this system does not track those.


Installation
------------

1. pip install -e git://github.com/jtrain/django-please-reply.git#egg=django-please-reply
2. add ``'please_reply'`` to your ``INSTALLED_APPS`` in your ``settings.py``
3. sync your database::
  
  python manage.py syncdb
4. if you use South you may migrate from a previous version.::
  
  python manage.py migrate please_reply

Usage
-----

This app hasn't been written yet ;)
