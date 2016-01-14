"""
Gobline ROS Shadow API.
"""

from __future__ import print_function

import logging
import xmlrpclib

from rosmaster.master_api import ROSMasterHandler
from rosmaster.master_api import apivalidate
from rosmaster.validators import is_service
from rosshadow.response import ResponseFactory

from rosshadow.configuration import load_shadow_config

NUM_WORKERS = 3  # number of threads we use to send publisher_update notifications

# keep logging functions 
_logger = logging.getLogger("goblin.shadow")

LOG_API = False


def mloginfo(msg, *args):
    """
    Info-level master log statements. These statements may be printed
    to screen so they should be user-readable.
    @param msg: Message string
    @type  msg: str
    @param args: arguments for msg if msg is a format string
    """
    # mloginfo is in core so that it is accessible to master and masterdata
    _logger.info(msg, *args)


def mlogwarn(msg, *args):
    """
    Warn-level master log statements. These statements may be printed
    to screen so they should be user-readable.
    @param msg: Message string
    @type  msg: str    
    @param args: arguments for msg if msg is a format string
    """
    # mloginfo is in core so that it is accessible to master and masterdata
    _logger.warn(msg, *args)
    if args:
        print("WARN: " + msg % args)
    else:
        print("WARN: " + str(msg))


swcfg = load_shadow_config()

METHODS = {}


def overwrite(fn):
    METHODS[fn.__name__] = fn
    return fn


class GoblinShadowHandler(ROSMasterHandler):
    """
    Goblin Shadow handler is a client-side local proxy of the original ROS Master.
    This additional intermediary provides some key features with slight overhead.
    """

    def __init__(self, master_uri, *args, **kwargs):
        super(GoblinShadowHandler, self).__init__(*args, **kwargs)
        self.master_proxy = xmlrpclib.ServerProxy(master_uri)

    def _dispatch(self, method, params):
        """
        Dispatch not-covered method to original ROS Master
        """
        print('{}{}'.format(method, params), '@', METHODS)
        if method in METHODS:
            code, explain, value = METHODS[method](self, *params)
        else:
            code, explain, value = getattr(self.master_proxy, method)(*params)
        return code, explain, value

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
        response = ResponseFactory.unknown_service()
        with self.ps_lock:
            cfg = swcfg.services.get_config(service)
            # try local
            if swcfg.localtype == cfg.priority:
                print(service)
            # fallback?
            elif cfg.fallback:
                if cfg is True:
                    pass
        return response.pack()
