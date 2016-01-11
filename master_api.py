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
from rosmaster.masther_api import STATUS, MSG, VAL

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
import rosmaster.masther_api.apivalidate

# import update tasks
from rosmaster.masther_api import publisher_update_task
from rosmaster.masther_api import service_update_task

###################################################
# Master Implementation
from rosmaster.masther_api import ROSMasterHandler

class GoblinShadowHandler(ROSMasterHandler):
    """
    Goblin Shadow handler is a client-side local proxy of the original ROS Master.
    This additional intermediary provides some key features with slight overhead.
    """
    pass
