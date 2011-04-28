"""
A series of views for people to reply to the RSVP invitation they recieved.

"""
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.utils.importlib import import_module

from please_reply import settings as backup_settings

HANDLERS = getattr(
            settings,
           'PLEASE_REPLY_VIEW_RESPONSE_HANDLERS',
            backup_settings.PLEASE_REPLY_VIEW_RESPONSE_HANDLERS)

_handlers = {}
def handler_for(response, default=None):
    if not _handlers:
        for name, handler in HANDLERS.items():
            module_name, func_name = handler.rsplit('.', 1)
            _handlers.update(
                    {name: getattr(import_module(module_name), func_name)}
            )
    return _handlers.get(response, default)

def replied_view(request, *args, **kwargs):
    """
    User has clicked on a valid invitiation response link, it could be any
    response code at all: 
        "accept",
        "reject",
        "yes",
        "no",
        "decline",
        "yes-thanks",
        "no-way-mate",
        .....

    The only thing that gives the `response` param (located as a kwargs) some
    meaning are the handlers defined in the settings.py file.

    PLEASE_REPLY_VIEW_RESPONSE_HANDLERS = {
            "accept": 'myproject.views.accept',
            "no"    : 'myproject.views.no' }

    There are of course, sensible defaults stored here, and you may point to a
    generic acceptance or declination handler.

    PLEASE_REPLY_VIEW_RESPONSE_HANDLERS = {
            "accept": 'please_reply.views.accept',
            "no"    : 'please_reply.views.decline' }
    """

    response = kwargs.pop("response")
    if not response:
        raise Http404

    handler = handler_for(response)
    if not handler:
        raise Http404

    response = handler(request, *args, **kwargs)
    if isinstance(response, HttpResponse):
        return response

    return direct_to_template(request, *args, **kwargs)

def generic_rejectance(request, *args, **kwargs):
    """
    The guest has rejected our proposal. 

    Interrogate the guest to find out why... :) just update the responded
    field.
    """
    return _generic_handler(
            request,
            (('responded', True),),
            *args, **kwargs
    )

def generic_acceptance(request, *args, **kwargs):
    """
    The user has accepted our proposal!

    update the `responded` and `attending` fields of the correct reply object.

    """
    return _generic_handler(
            request,
            (('attending', True), ('responded', True)),
            *args, **kwargs
    )

def _generic_handler(request, fields, *args, **kwargs):

    object_name = kwargs.get('template_object_name', 'object')
    guest_reply = kwargs.get(object_name)
    if not guest_reply:
        raise Http404


    for fieldname, fieldvalue in fields:
        setattr(guest_reply, fieldname, fieldvalue)

    guest_reply.save()

    return guest_reply


