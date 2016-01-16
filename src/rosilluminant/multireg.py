"""
ROS Illuminant Multiple Register Implementation

Supporting multi-registering & load-balancing
"""
import heapq
from collections import defaultdict
from functools import total_ordering

from rosmaster.registrations import Registrations, RegistrationManager
import rosmaster.exceptions


@total_ordering
class ServiceRecord(object):
    __slots__ = ('counter', 'caller_id', 'service_api')

    def __init__(self, caller_id, service_api):
        self.counter = 0
        self.caller_id = caller_id
        self.service_api = service_api

    def __lt__(self, other):
        if isinstance(other, ServiceRecord):
            return self.counter < other.counter
        raise TypeError('Cannot compare ServiceRecord wit {}'.format(type(other)))

    def __eq__(self, other):
        if isinstance(other, ServiceRecord):
            return self.caller_id == other.caller_id and self.service_api == other.service_api
        raise TypeError('Cannot compare ServiceRecord wit {}'.format(type(other)))

    def count(self, value=None):
        if value is None:
            self.counter += 1
        else:
            self.counter = value

    def match(self, caller_id, service_api):
        return self.caller_id == caller_id and self.service_api == service_api

    def value(self):
        return self.caller_id, self.service_api


class ServiceHeap:
    def __init__(self, record_type=None):
        self.record_type = record_type if record_type is not None else ServiceRecord
        self.heap = []

    def insert(self, caller_id, service_api):
        if not self.has(caller_id, service_api):
            heapq.heappush(self.heap, self.record_type(caller_id, service_api))

    def has(self, caller_id, service_api):
        for record in self.heap:
            if record.match(caller_id, service_api):
                return True
        else:
            return False

    def remove(self, caller_id, service_api):
        for record in self.heap:
            if record.match(caller_id, service_api):
                record.count(-1)
                heapq.heapify(self.heap)
                heapq.heappop(self.heap)
                break

    def minimal_update(self):
        value = self.heap[0].value()
        self.heap[0].count()
        heapq.heapify(self.heap)
        return value

    def __len__(self):
        return len(self.heap)

    def __nonzero__(self):
        return len(self.heap) != 0


class MultiRegistrations(Registrations):
    def __init__(self, type_):
        """
        ctor.
        @param type_: one of [ TOPIC_SUBSCRIPTIONS,
        TOPIC_PUBLICATIONS, SERVICE, PARAM_SUBSCRIPTIONS ]
        @type  type_: int
        """
        super(MultiRegistrations, self).__init__(type_)
        self.map = defaultdict(list)  # {key: [(id, api)]}

    def register(self, key, caller_id, caller_api, service_api=None):
        """
        Add caller_id into the map as a provider of the specified
        service (key).  caller_id must not have been previously
        registered with a different caller_api.

        Subroutine for managing provider map data structure (essentially a multimap).
        @param key: registration key (e.g. topic/service/param name)
        @type  key: str
        @param caller_id: caller_id of provider
        @type  caller_id: str
        @param caller_api: API URI of provider
        @type  caller_api: str
        @param service_api: (keyword) ROS service API URI if registering a service
        @type  service_api: str
        """
        # ignoring that only ONE service could be running
        self.map[key].append((caller_id, caller_api))
        if service_api:
            # TODO: find out whether some code dependents on this `is None`
            if self.service_api_map is None:
                self.service_api_map = defaultdict(ServiceHeap)
            self.service_api_map[key].insert(caller_id, service_api)
        elif self.type == Registrations.SERVICE:
            raise rosmaster.exceptions.InternalException("service_api must be specified for Registrations.SERVICE")

    def unregister(self, key, caller_id, caller_api, service_api=None):
        """
        Remove caller_id from the map as a provider of the specified service (key).
        Subroutine for managing provider map data structure, essentially a multimap
        @param key: registration key (e.g. topic/service/param name)
        @type  key: str
        @param caller_id: caller_id of provider
        @type  caller_id: str
        @param caller_api: API URI of provider
        @type  caller_api: str
        @param service_api: (keyword) ROS service API URI if registering a service
        @type  service_api: str
        @return: for ease of master integration, directly returns unregister value for
        higher-level XMLRPC API. val is the number of APIs unregistered (0 or 1)
        @rtype: code, msg, val
        """
        # if we are unregistering a topic, validate against the caller_api
        if service_api:
            # validate against the service_api
            if self.service_api_map is None:
                return 1, "[%s] is not a provider of [%s]" % (caller_id, key), 0
            if not self.service_api_map[key].has(caller_id, service_api):
                return 1, "[%s] is no longer the current service api handle for [%s]" % (service_api, key), 0
            else:
                self.service_api_map[key].remove(caller_id, service_api)
            # caller_api is None for unregister service, so we can't validate as well
            return 1, "Unregistered [%s] as provider of [%s]" % (caller_id, key), 1
        elif self.type == Registrations.SERVICE:
            raise rosmaster.exceptions.InternalException("service_api must be specified for Registrations.SERVICE")
        else:
            providers = self.map.get(key, [])
            if (caller_id, caller_api) in providers:
                providers.remove((caller_id, caller_api))
                if not providers:
                    del self.map[key]
                return 1, "Unregistered [%s] as provider of [%s]" % (caller_id, key), 1
            else:
                return 1, "[%s] is not a known provider of [%s]" % (caller_id, key), 0

    def get_service_api(self, service):
        """
        Lookup service API URI. NOTE: this should only be valid if type==SERVICE as
        service Registrations instances are the only ones that track service API URIs.
        @param service: service name
        @type  service: str
        @return str: service_api for registered key or None if
        registration is no longer valid.
        @type: str
        """
        service_api = None
        heap = self.service_api_map[service]
        if heap:  # if not empty, return LRU instance and update the heap
            _, service_api = heap.minimal_update()
        return service_api


class MultiRegistrationManager(RegistrationManager):
    def __init__(self, thread_pool):
        super(MultiRegistrationManager, self).__init__(thread_pool)
        self.services = MultiRegistrations(Registrations.SERVICE)
