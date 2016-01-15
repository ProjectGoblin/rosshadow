"""
Response structure
"""


class Response(object):
    __slots__ = ('status', 'msg', 'value')

    def __init__(self, status, msg, value):
        self.status = status
        self.msg = msg
        self.value = value

    def __repr__(self):
        return 'Response({!r}, {!r}, {!r})'.format(self.status, self.msg, self.value)

    def __str__(self):
        return self.__repr__()

    def pack(self):
        return self.status, self.msg, self.value

    def is_success(self):
        return self.status == 1


class ResponseFactory:
    @staticmethod
    def unknown_service(service):
        return Response(-1,
                        '[Goblin][Shadow] Unknown service provider: {}'.format(service),
                        r'')

    @staticmethod
    def uri_found(key, uri):
        return Response(1, key, uri)

    @staticmethod
    def service_reg(caller_id, service):
        return Response(1, "Registered [%s] as provider of [%s]"%(caller_id, service), 1)
