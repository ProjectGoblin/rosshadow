"""
Gobline ROS Shadow API.
"""

from __future__ import print_function

import os
import sys
import logging
import threading
import time
import traceback

from rosgraph.xmlrpc import XmlRpcHandler

import rosgraph.names
from rosgraph.names import resolve_name
import rosmaster.paramserver
import rosmaster.threadpool

from rosmaster.util import xmlrpcapi
from rosmaster.registrations import RegistrationManager
from rosmaster.validators import non_empty, non_empty_str, not_none, is_api, is_topic, is_service, valid_type_name, valid_name, empty_or_valid_name, ParameterInvalid

NUM_WORKERS = 3 #number of threads we use to send publisher_update notifications

# import original return code slots
from rosmaster.master_api import STATUS, MSG, VAL

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
    #mloginfo is in core so that it is accessible to master and masterdata
    _logger.info(msg, *args)

def mlogwarn(msg, *args):
    """
    Warn-level master log statements. These statements may be printed
    to screen so they should be user-readable.
    @param msg: Message string
    @type  msg: str    
    @param args: arguments for msg if msg is a format string
    """
    #mloginfo is in core so that it is accessible to master and masterdata
    _logger.warn(msg, *args)
    if args:
        print("WARN: " + msg % args)
    else:
        print("WARN: " + str(msg))

# import apivalidate
from rosmaster.master_api import apivalidate

# import update tasks
from rosmaster.master_api import publisher_update_task
from rosmaster.master_api import service_update_task

# import shadow configuration
from rosshadow.configuration import load_shadow_config

swcfg = load_shadow_config()

###################################################
# Master Implementation
from rosmaster.master_api import ROSMasterHandler

class GoblinShadowHandler(ROSMasterHandler):
    """
    Goblin Shadow handler is a client-side local proxy of the original ROS Master.
    This additional intermediary provides some key features with slight overhead.
    """
    @apivalidate(0, (is_service('service'),))
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
        response = (-1, '[Goblin][Shadow] Internal Failure', None)
        with self.ps_lock:
            cfg = swcfg.services.get_config(service)
            # try local
            if swcfg.localtype == cfg.priority:
                print(service)
            # fallback?
            elif cfg.fallback:
                if cfg is True:
                    pass
        return response
