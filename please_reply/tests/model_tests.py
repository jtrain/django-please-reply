from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.contrib.contenttypes.models import ContentType

from please_reply import exceptions
from please_reply.tests.models import Event
from please_reply.models import ReplyList, Reply

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

class ReplyManagementTest(RelateEventsToGuests):
    """
    Test the management methods on the reply model.
    """

    def test_reply_manager_reply_to_event(self):
        """
        Manager should make the guest as attending or not attending the event
        and save.
        """

        
        # jill wasn't invited assert this fails.
        self.assertRaises(exceptions.NotInvited,
                         Reply.objects.reply_to_event_for,
                            event('jenga'),
                            user('jill'),
                            attending=True
        )

        Reply.objects.reply_to_event_for(
            event('jenga'),
            user('sally'),
            attending=True,
        )
        
        self.assertEqual(
                [user('sally')],
                guests(ReplyList.objects.get_confirmed_guests_for(
                       event('jenga')))
        )

class ReplyListManagementTest(RelateEventsToGuests):
    """
    Test the management methods on the replylist.

    """

    def test_replylist_manager_confirmed_guests(self):
        """
        Manager should return a list of all confirmed guests once a guest
        has replied as attending.
        """

        # no one has replied yet.
        for event_ in self.events:
            self.assertEqual([],
                list(ReplyList.objects.get_confirmed_guests_for(event_))
            )


        jenga = event('jenga')
        # let sven reply as attending.
        Reply.objects.reply_to_event_for(
                jenga,
                user('sven'),
                attending=True
        )

        # now check that there is a confirmed guest.
        get_confirmed_guests_for = ReplyList.objects.get_confirmed_guests_for
        self.assertEqual(
                [user('sven')],
                guests(get_confirmed_guests_for(jenga))
        )

    def test_replylist_manager_guests(self):
        """
        Manager should return all invited guests for an event.

        """
        jenga = event('jenga')

        get_invited_guests_for = ReplyList.objects.get_invited_guests_for
        self.assertEqual(
                sortname([user('sven'), user('sally')]),
                sortname(guests(get_invited_guests_for(jenga)))
        )

