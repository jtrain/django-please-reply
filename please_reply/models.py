import random
import zlib
import base64

from django.db import models
from django.db.models import get_model
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from please_reply import settings as backup_settings
from please_reply.exceptions import NotInvited, InvalidHash

USER_MODEL = getattr(
                settings,
                'PLEASE_REPLY_USER_MODEL',
                backup_settings.PLEASE_REPLY_USER_MODEL)

class ReplyListManager(models.Manager):
    """
    Defines helper functions to get all attendees for an event.

    """

    def is_guest_attending(self, event, guest):
        """
        Returns true if the guest is marked as attending this event.

        """
        matching_guest = self.get_replylist_for(event
            ).replies.filter(attending=True, guest=guest)
        return any(matching_guest.all())

    def get_confirmed_guests_for(self, event):
        """
        return all attending=True replies for the given event.
        """
        return self.get_replylist_for(event
                ).replies.filter(attending=True)

    def get_invited_guests_for(self, event):
        """
        Return all Reply models for the given event.
        """
        return self.get_replylist_for(event
               ).replies.all()

    def get_replylist_for(self, event):
        """
        Return the replylist for the given event.
        """
        event_type = ContentType.objects.get_for_model(event)

        return self.get_query_set().get(
                object_id=event.pk,
                content_type=event_type)

    def create_replylist(self, event, guests=None):
        """
        Create a new reply list with optional guest-list.

        Running a second time with the some of the same guests will not change
        the replies for the existing guests but will add new blank replies for
        the new guests.
        """
        if guests is None:
            guests = []

        content_type = ContentType.objects.get_for_model(event)

        replylist, created = self.model.objects.get_or_create(
                    object_id=event.pk,
                    content_type=content_type
        )

        replylist.save()

        for guest in guests:

            emptyreply, created = Reply.objects.get_or_create(
                    replylist=replylist,
                    guest=guest
            )

            if created:
                emptyreply.attending=False
                emptyreply.responded=False
                emptyreply.save()

        return replylist

class ReplyList(models.Model):
    """
    A group of replies for an event.
    """

    # event instance.
    object_id = models.CharField(max_length=1023)
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = ReplyListManager()

    class Meta:
        verbose_name = _("reply list")
        verbose_name_plural = _("reply lists")
        ordering = ("content_type", "-object_id")
        unique_together = ('object_id', 'content_type')

    def __unicode__(self):
        return u"replies for %s" % (
                    self.content_object
        )

def make_simple_filter_manager(**filter_kwargs):
    """
    Factory function returns Manager class that filters
    results by the keywords given in filter_kwargs.
    """

    class FilteredReplyManager(models.Manager):
        def get_query_set(self):
            return super(FilteredReplyManager, self).get_query_set(
                    ).filter(**filter_kwargs)

    return FilteredReplyManager

class ReplyManager(models.Manager):
    """
    Some convenience methods for marking a guest as attending an event.

    """

    def reply_to_event_for(self, event, guest, attending):
        """
        Set guest's reply to attending (true or false) for the replylist
        matching the event.

        """
        replylist = ReplyList.objects.get_replylist_for(event)
        try:
            guest = self.model.objects.get(
                        replylist=replylist,
                        guest=guest)
        except self.model.DoesNotExist:
            raise NotInvited("%s wasn't invited to %s" %
                                (guest, event))

        guest.attending = attending
        guest.responded = True
        guest.save()
        return guest

class Reply(models.Model):
    """
    A single guest's reply to an event.
    """

    replylist = models.ForeignKey(
                'ReplyList',
                related_name="replies",
                verbose_name=_("reply to list")
    )

    guest = models.ForeignKey(
                get_model(*USER_MODEL.split(".")),
                verbose_name=_("guest")
    )
                
    attending = models.BooleanField(
                _("attending"),
                default=False
    )

    responded = models.BooleanField(
                _("responded"),
                default=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # custom managers.
    objects = ReplyManager()
    confirmed_guests = make_simple_filter_manager(attending=True)()
    not_responded = make_simple_filter_manager(responded=False)()
    
    def generate_userhash(self, salt):
        """
        create XOR encrypted and base64 encoded text version of the guest__pk.
        """
        return encode_userhash(self.guest.pk, self.replylist.pk, salt)

    class Meta:
        verbose_name = _("reply")
        verbose_name_plural = _("replies")
        ordering = ("replylist", "-responded", "-attending", "guest")
        unique_together = ('guest', 'replylist')

    def __unicode__(self):
        return u"%s is%s attending %s" % (
                    self.guest,
                    '' if self.attending else ' not',
                    self.replylist.content_object
        )

#----------------------------------------------------------------------
# Utilities
def tinycode(key, text, reverse=False):
    """
    an XOR type encryption routine taken from 
    http://code.activestate.com/recipes/266586-simple-xor-keyword-encryption/

    This isn't a secure technique, I am only using it to slightly obscure an
    otherwise obvious use of user.id in the uri. I know I could use a UUID for
    this purpose, but I didn't want to add uuid as a dependancy for this
    project.

    """
    rand = random.Random(key).randrange
    if not reverse:
        text = zlib.compress(text)
    text = ''.join([chr(ord(elem)^rand(256)) for elem in text])
    if reverse:
        text = zlib.decompress(text)
    return text



def decode_userhash(userhash, reply_list_id, salt):
    """
    Decode and return the user-pk value.
    Assume the unhashed text has the form:

    userpk.

    and was generated with key

    salt%%reply_list_id

    we are in big trouble if salt has %% in it!!.
    so we assume they are not present.
    """

    reply_list_id = str(reply_list_id).replace("%%", "")
    salt          = str(salt).replace("%%", "")

    key = "%%".join([salt, reply_list_id])
    userhash = base64.urlsafe_b64decode(str(userhash))

    try:
        return tinycode(key, userhash, reverse=True)
    except zlib.error:
        raise InvalidHash('attempted to decrypt %s with invalid key %s' %
                                (userhash, key))
    
def encode_userhash(userpk, reply_list_id, salt):
    """
    Return a base64 XOR encrypted text using a key of:

    salt%%reply_list_id

    where any '%%' has been removed from salt and reply_list_id
    """

    reply_list_id = unicode(reply_list_id).replace("%%", "")
    salt          = unicode(salt).replace("%%", "")

    key = "%%".join([salt, reply_list_id])

    userhash = tinycode(key, str(userpk))
    return base64.urlsafe_b64encode(userhash)


