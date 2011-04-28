from functools import partial

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from please_reply import exceptions
from please_reply import settings as backup_settings
from please_reply.tests.models import Event
from please_reply.models import ReplyList, Reply, encode_userhash


#--------------------------------------------------------------
# Constants

SALT = getattr(
          settings,
         'PLEASE_REPLY_SECRET_SALT',
          backup_settings.PLEASE_REPLY_SECRET_SALT)

#--------------------------------------------------------------
# helper functions

def event(title):
    return Event.objects.get(title=title)

def user(username):
    return User.objects.get(username=username)

def guests(replies):
    return [r.guest for r in replies]

def sortname(lst):
    return sorted(lst, key=lambda x:x.username)

#--------------------------------------------------------------
# Test Base Cases

class ManyUsersBaseCase(TestCase):
    """
    A bunch of users that may be invited to attend an event.

    """

    def setUp(self):
        super(ManyUsersBaseCase, self).setUp()

        self.client = Client()

        users = ['jim', 'jill', 'sven', 'gertrude', 'sally']
        for user in users:
            User.objects.create_user(
                            user, '%s@example.com' % user, user)


class CreateEventsBaseCase(ManyUsersBaseCase):
    """
    A bunch of events that can be attended.
    """

    def setUp(self):
        super(CreateEventsBaseCase, self).setUp()

        self.events = []
        for event in ["bbq", "jenga", "cleaning"]:
            e = Event(title=event)
            e.save()
            self.events.append(e)

class RelateEventsToGuests(CreateEventsBaseCase):

    def setUp(self):
        super(RelateEventsToGuests, self).setUp()

        for event in self.events:

            # sally is on every guest list, congrats sal.
            guests = [user('sally')]

            # sven is a jenga master, auto invite for him.
            if event.title == 'jenga':
                guests.append(user('sven'))

            ReplyList.objects.create_replylist(
                    event,
                    guests=guests
            )
class ReplyFormReply(RelateEventsToGuests):
    """
    Test that guest can reply using the reply form,
    and that this will update their status.

    """

    def test_view_event_reply_form_accept(self):
        """
        Sally uses the reply form to accept the invitation to the
        bbq.

        """

        _event = event('bbq')
        _user = user('sally')

        accept_response = self._user_replies_to_event(
                    _user,
                    _event,
                    'yes'
        )

        self.assertEqual(accept_response.status_code, 200)

        self.assertTrue(
                ReplyList.objects.is_guest_attending(_event, _user))

        self.assertTrue(
                Reply.objects.get(guest=_user, attending=True).responded)

    def test_user_changes_mind(self):
        """
        User changes mind many times on whether or not to attend.

        """
        _event = event('jenga')
        _user = user('sven')

        self._user_replies_to_event(
                _user, _event, "no")

        self.assertFalse(
                ReplyList.objects.is_guest_attending(_event, _user))

        self.assertTrue(
                Reply.objects.get(guest=_user, attending=False).responded)

        self._user_replies_to_event(
                _user, _event, "yes")

        self.assertTrue(
                ReplyList.objects.is_guest_attending(_event, _user))

    def test_no_one_elses_records_change(self):
        """
        One person accepting does not affect any other attendees.

        """
        self._user_replies_to_event(user('sally'), event('jenga'), "yes")

        self.assertEqual(
            sorted(Reply.confirmed_guests.all()),
            sorted(Reply.objects.filter(guest=user('sally'), attending=True))
        )

        self.assertEqual(Reply.confirmed_guests.count(), 1)
        self.assertEqual(Reply.not_responded.count(), 3)

    def _user_replies_to_event(self, user, event, response, **kws):

        replylist = ReplyList.objects.get_replylist_for(event)
        slug = event.slug
        userhash = encode_userhash(user.pk, replylist.pk, SALT)

        uri = reverse('please_reply_replied',
                kwargs=dict(
                    slug=event.slug,
                    reply_list_id=replylist.pk,
                    user_hash=userhash,
                    response=response,
                )
        )
        return self.client.get(uri)

class ReplyFormViewTest(RelateEventsToGuests):
    """
    Test that a user can reply to an event using a view.
    """
    def test_view_event_returns_200_for_invited_guest(self):
        """
        Test viewing a reply_form returns a 200 for an invited guest.
        """
        self._user_views_event_statuscode_expected(
                    user('sally'),
                    event('bbq'),
                    200
        )

    def test_view_event_fails_for_notinvited_guest(self):
        """
        sven hasn't been invited to the bbq, can he attend?

        """
        self._user_views_event_statuscode_expected(
                    user('sven'),
                    event('bbq'),
                    404
        )

    def test_view_event_fails_for_bad_slug(self):
        """
        sally was invited, but the event slug is wrong.

        """
        self._user_views_event_statuscode_expected(
                    user('sally'),
                    event('bbq'),
                    404,
                    slug='bbq_for_me',
        )

    def test_view_event_fails_for_missing_uri_info(self):
        """
        Someone hand crafted a uri without one of the required params.

        """
        valid_url_bits = {'slug': 'bbq', 'reply_list_id': '1',
                          'user_hash': 'aL8-8Ozuc-XB'}
        uri = '/rsvp/%(slug)s-%(reply_list_id)s/%(user_hash)s/'

        # prove that this is a valid uri!
        self._user_views_event_statuscode_expected(
                    user('sally'),
                    event('bbq'),
                    200,
                    uri=uri % valid_url_bits,
        )

        for missing_bit in valid_url_bits:
            value = valid_url_bits.pop(missing_bit)
            valid_url_bits[missing_bit] = ''

            self._user_views_event_statuscode_expected(
                    user('sally'),
                    event('bbq'),
                    404,
                    uri=uri % valid_url_bits,
            )
            valid_url_bits[missing_bit] = value

    def test_view_event_fails_for_invalid_hash(self):
        """
        Someone tries to use any old hash value, note that is still possible
        for anyone to stumble across another valid value by chance.

        """
        self._user_views_event_statuscode_expected(
                    user('sally'),
                    event('bbq'),
                    404,
                    userhash='aL8-8Ozuc-XE',
        )
    #----------------------------------------------------------
    # helpers.

    def assertStatusCode(self, response, code):
        self.assertEqual(response.status_code, code)

    def _user_views_event_statuscode_expected(self, user, event, code, **kws):
        self._user_views_event(user, event,
                partial(self.assertStatusCode, code=code), **kws)

    def _user_views_event(self, user, event, response_test, **kws):
        slug = kws.pop('slug', event.slug)

        replylist = ReplyList.objects.get_replylist_for(event)

        userhash = kws.pop('userhash',
                            encode_userhash(user.pk, replylist.id, SALT)
        )

        uri = kws.pop('uri', reverse('please_reply_reply_form',
                                kwargs=dict(
                                    slug=slug,
                                    reply_list_id=replylist.pk,
                                    user_hash=userhash
                                )
                            )
        )

        response = self.client.get(uri)
        response_test(response)

