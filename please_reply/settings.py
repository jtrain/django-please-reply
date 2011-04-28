PLEASE_REPLY_USER_MODEL = "auth.user"

PLEASE_REPLY_SECRET_SALT = 's3cR3t547T'

PLEASE_REPLY_VIEW_RESPONSE_HANDLERS = {
        'accept': 'please_reply.views.generic_acceptance',
        'decline':'please_reply.views.generic_rejectance',
}
