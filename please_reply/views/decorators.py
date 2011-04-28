"""
A series of views for people to reply to the RSVP invitation they recieved.

"""
from functools import wraps

from django.conf import settings
from django.db.models import get_model
from django.http import Http404
from django.shortcuts import get_object_or_404

from please_reply import settings as backup_settings
from please_reply.models import Reply, ReplyList, decode_userhash
from please_reply.exceptions import InvalidHash

#-----------------------------------------------------------------------------
# settings.

SECRET_SALT = getattr(
                settings,
               'PLEASE_REPLY_SECRET_SALT',
                backup_settings.PLEASE_REPLY_SECRET_SALT)

#----------------------------------------------------------------------------
# decorators

def validate_please_reply_uri(view):
    """
    wraps a view function and checks the following expected kws.

    expected kws:

        user_hash: 

            an md5 hexdigest of the 

                PLEASE_REPLY_SECRET_SALT + reply_list_id + user_pk

            this is used to uniquely identify the user that was invited to the
            event and to discourage people checking who else is attending the
            event by guessing other user primary keys if that was used in
            the url directly.

        reply_list_id:
            
            the id for the ReplyList that the user is replying for.
        
        [slug]:

            a field that exists on your Event model (whatever it is) that
            uniquely identifies it. Top marks if it is a slug, because they are
            human readable, but you could name this parameter id or pk if you like.

            e.g. for the event model:

                class WeddingEvent(models.Model):

                    title = models.CharField(max_length=255)
                    wedding_slug = models.SlugField(max_length=512, unique=True)
                
                and wedding_slug is unique, we can use the following url
                pattern:

                    r'^(?<wedding_slug>[-\w]+).....
            
                note that I used wedding_slug in place of slug.

    """

    @wraps(view)
    def inner(request, *args, **kws):

        user_hash = kws.get('user_hash', None)
        reply_list_id = kws.get('reply_list_id', None)
        slug_field = kws.pop('slug_field', 'slug')
        event_identifier = kws.get(slug_field, None)
        template_object_name = kws.pop('template_object_name', 'object')

        # fail early if one of the required params wasn't provided.
        if not (user_hash and reply_list_id and event_identifier):
            raise Http404
    
        try:
            userpk = decode_userhash(user_hash, reply_list_id, SECRET_SALT)
        except InvalidHash:
            raise Http404
    
        replylist = get_object_or_404(ReplyList, id=reply_list_id)
    
        replylist_event_value = getattr(replylist.content_object, slug_field)
        if  unicode(replylist_event_value) != unicode(event_identifier):
            raise Http404
    
        guestreply = get_object_or_404(
                        Reply,
                        guest__pk=userpk,
                        replylist__id=reply_list_id
        )

        kws.update({template_object_name: guestreply})

        extra_context = kws.get('extra_context', {})
        extra_context.update(
            dict((k, v)
            for (k, v) in kws.items()
            if k in (slug_field,
                     'reply_list_id',
                     'user_hash',
                     template_object_name))
        )

        kws['extra_context'] = extra_context

        return view(request, *args, **kws)

    return inner
    
