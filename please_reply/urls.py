from django.conf.urls.defaults import url, patterns, include
from django.views.generic.simple import direct_to_template

from please_reply.views.decorators import validate_please_reply_uri
from please_reply.views import replied_view
from please_reply.models import Reply

urlpatterns = patterns('',

        url(r'^(?P<slug>[-\w]+)\-(?P<reply_list_id>[-\w]+)/(?P<user_hash>[-\w]+)/$',
            validate_please_reply_uri(direct_to_template), {
            'template'            : 'please_reply/reply_form.html',
            'template_object_name': 'object',
            'slug_field'          : 'slug',
            'extra_context'       : {}
            }, name='please_reply_reply_form'),



                                                # param name     example.
                                                #-----------     ---------------

        url((r'^(?P<slug>[-\w]+)\-'             # event-slug-    (bbq-at-beach-)
             r'(?P<reply_list_id>[-\w]+)/'      # reply_list_id/ (1/)
             r'(?P<user_hash>[-\w]+)/'          # user_hash/     (asg8sgl-2/)
             r'(?P<response>[-\w]+)/$'),        # response/      (accept/)

            validate_please_reply_uri(replied_view), {
            'template'            : 'please_reply/replied.html',
            'template_object_name': 'object',
            'slug_field'          : 'slug',
            'extra_context'       : {},
            }, name='please_reply_replied'),
)
