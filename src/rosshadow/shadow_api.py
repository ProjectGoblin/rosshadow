"""
Gobline ROS Shadow API.
"""

from __future__ import print_function

import threading
import xmlrpclib
import socket

from rosshadow.logger import generate_handler as _getLogger
from rosmaster.master_api import apivalidate
from rosmaster.validators import is_service, is_api
from rosilluminant.multireg import MultiRegistrationManager
from rosmaster.threadpool import MarkedThreadPool
from rosshadow.response import ResponseFactory
from rosshadow.combinator import *

from rosshadow.configuration import load_shadow_config
import rosshadow.configuration as shadowcfg

NUM_WORKERS = 3  # number of threads we use to send publisher_update notifications

swcfg = load_shadow_config()

METHODS = {}

logger = _getLogger('Goblin::Shadow::API')


def overwrite(fn):
    METHODS[fn.__name__] = fn
    return fn


class GoblinShadowHandler(object):
    """
    Goblin Shadow handler is a client-side local proxy of the original ROS Master.
    This additional intermediary provides some key features with slight overhead.
    """

    def __init__(self, master_uri, num_works, timeout=None):
        # Running status
        self.shadow_uri = None
        self.master_uri = master_uri
        self._caller_id = '/Goblin/Shadow/unbind'
        self._running = True

        # Inner fields
        socket.setdefaulttimeout(timeout)
        self.thread_pool = MarkedThreadPool(num_works)
        self.ps_lock = threading.Condition(threading.Lock())
        self.reg_manager = MultiRegistrationManager(self.thread_pool)
        self.master_proxy = xmlrpclib.ServerProxy(master_uri)
        # TODO: support all local nodes
        self.services = self.reg_manager.services
        # TODO: support local param-server caches

    # APIs for running XML-RPC
    def _shutdown(self, reason=''):
        """
        Forked from ROSMasterHandler
        @param reason:
        @return:
        """
        if self.thread_pool is not None:
            self.thread_pool.join_all(wait_for_tasks=False, wait_for_threads=False)
            self.thread_pool = None
        self._running = False

    def _ready(self, uri):
        """
        Impl standard XML-RPC API to update URI
        @param uri:
        @return:
        """
        self.shadow_uri = uri
        self._caller_id = '/Goblin/Shadow/unbind_{}'.format(uri)

    def _dispatch(self, method, params):
        """
        Dispatch not-covered method to original ROS Master
        """
        logger.info('Required: {}{}'.format(method, params))
        if method in METHODS:
            logger.debug('--  LOCAL')
            status, msg, value = METHODS[method](self, *params)
            logger.debug('>>  LOCAL {}'.format((status, msg, value)))
        else:
            logger.debug('-- REMOTE: {!r}'.format(getattr(self.master_proxy, method)))
            status, msg, value = getattr(self.master_proxy, method)(*params)
            logger.debug('>> REMOTE: {}'.format((status, msg, value)))
        return status, msg, value

    def is_running(self):
        return self._running

    # private methods for running Shadow
    def _lookup_local_service(self, service):
        uri = None
        with self.ps_lock:
            uri = self.services.get_service_api(service)
        return uri

    def _lookup_remote_service(self, service):
        return self.master_proxy.lookupService(self._caller_id, service)

    def _reg_local_service(self, service, caller_id, caller_api, service_api):
        logger.info('-- Reg Local {} {}'.format(service, service_api))
        with self.ps_lock:
            self.reg_manager.register_service(service, caller_id, caller_api, service_api)
            logger.info("+SERVICE [%s] %s %s", service, caller_id, caller_api)

    def _reg_remote_service(self, *args):
        r = self.master_proxy.registerService(*args)
        logger.info('-- Reg Remote {}'.format(r))

    def _unreg_local_service(self, caller_id, service, service_api):
        with self.ps_lock:
            self.reg_manager.unregister_service(service, caller_id, service_api)

    def _unreg_remote_service(self, *args):
        r = self.master_proxy.unregisterService(*args)
        logger.info('-- Unreg Remote {}'.format(r))

    # Overwritten APIs
    @apivalidate(0, (is_service('service'),))
    @overwrite
    def lookupService(self, caller_id, service):
        """
        Lookup all provider of a particular service in following rules:
        1. Local/Auto/Unlabeled
            1. Use local services if possible.
            2. Otherwise, use remote services.
        2. Remote
            1. If average time cost belows the balance-curve, use remote services.
            2. Otherwise, use remote services if possible.
        @param caller_id str: ROS caller id
        @type  caller_id: str
        @param service: fully-qualified name of service to lookup.
        @type: service: str
        @return: (code, message, serviceUrl). service URL is provider's
        ROSRPC URI with address and port.  Fails if there is no provider.
        @rtype: (int, str, str)
        """
        uri = None
        cfg = swcfg.services.get_config(service)

        def skeleton(x, y):
            fallback_p = const(bool(cfg.fallback))
            # TODO: support fallback list
            return on_fallback(x, y, fallback_p, success_uri)

        # local?
        if swcfg.localtype == cfg.priority:
            fn = skeleton(self._lookup_local_service, self._lookup_remote_service)
        else:
            fn = skeleton(self._lookup_remote_service, self._lookup_local_service)
        uri = fn(service)
        if success_uri(uri):
            return ResponseFactory.uri_found(service, uri).pack()
        else:
            return ResponseFactory.unknown_service(service).pack()

    @apivalidate(0, (is_service('service'), is_api('service_api'), is_api('caller_api')))
    @overwrite
    def registerService(self, caller_id, service, service_api, caller_api):
        """
        Forked from ROSMasterHandler.
        Register the caller as a provider of the specified service.
        0. If service is `remote-only`, register with ROS Master
        1. If Service is `local-only`, register with current shadow instance.
        2. Otherwise, register with both sides.
        @param caller_id str: ROS caller id
        @type  caller_id: str
        @param service: Fully-qualified name of service
        @type  service: str
        @param service_api: Service URI
        @type  service_api: str
        @param caller_api: XML-RPC URI of caller node
        @type  caller_api: str
        @return: (code, message, ignore)
        @rtype: (int, str, int)
        """
        cfg = swcfg.services.get_config(service)
        if not cfg.is_local_only():
            self._reg_remote_service(caller_id, service, service_api, caller_api)
        if not cfg.is_remote_only():
            self._reg_local_service(caller_id, service, service_api, caller_api)
        return ResponseFactory.service_reg(caller_id, service).pack()

    @apivalidate(0, (is_service('service'), is_api('service_api')))
    @overwrite
    def unregisterService(self, caller_id, service, service_api):
        """
        Forked from ROSMasterHandler.
        Unregister the caller as a provider of the specified service.
        @param caller_id str: ROS caller id
        @type  caller_id: str
        @param service: Fully-qualified name of service
        @type  service: str
        @param service_api: API URI of service to unregister. Unregistration will only occur if current
           registration matches.
        @type  service_api: str
        @return: (code, message, numUnregistered). Number of unregistrations (either 0 or 1).
           If this is zero it means that the caller was not registered as a service provider.
           The call still succeeds as the intended final state is reached.
        @rtype: (int, str, int)
        """
        cfg = swcfg.services.get_config(service)
        if not cfg.is_local_only():
            self._unreg_remote_service(caller_id, service, service_api)
        if not cfg.is_remote_only():
            self._unreg_local_service(caller_id, service, service_api)
        return ResponseFactory.service_unreg(caller_id, service).pack()
