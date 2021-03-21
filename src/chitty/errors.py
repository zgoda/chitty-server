E_REASON_MALFORMED = 'E_REASON_MALFORMED'
E_REASON_TYPE_INVALID = 'E_REASON_TYPE_INVALID'
E_REASON_NOTREG = 'E_REASON_NOTREG'
E_REASON_TOPIC_SYSTEM = 'E_REASON_TOPIC_SYSTEM'

E_WEB_NOTFOUND = '404'
E_WEB_BADREQ = '400'


class ChatMessageException(Exception):
    pass


class MessageRoutingError(ChatMessageException):
    pass


class MessageFormatError(ChatMessageException):
    pass
