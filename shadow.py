"""
Gobline Shadow
"""

import logging
import time
import os

import rosgraph.xmlrpc

import rosshadow.shadow_api

from rosmaster.master import DEFAULT_MASTER_PORT
DEFAULT_SHADOW_PORT=11411 #default port for master's to bind to

class Shadow(object):
    
    def __init__(self,
                 shadow_port=DEFAULT_SHADOW_PORT,
                 num_workers=rosshadow.shadow_api.NUM_WORKERS,
                 master_uri=None):
        self.port = shadow_port
        self.num_workers = num_workers
        if master_uri is None:
            self.master_uri = os.environ['ROS_MASTER_URI']
        else:
            self.master_uri = master_uri
        
    def start(self):
        """
        Start the Goblin Shadow.
        """
        self.handler = None
        self.master_node = None
        self.shadow_node = None
        self.uri = None

        handler = rosshadow.shadow_api.GoblinShadowHandler(self.master_uri, self.num_workers)
        shadow_node = rosgraph.xmlrpc.XmlRpcNode(self.port, handler)
        shadow_node.start()

        # poll for initialization
        while not shadow_node.uri:
            time.sleep(0.0001) 

        # save fields
        self.handler = handler
        self.shadow_node = shadow_node 
        self.uri = shadow_node.uri
       
        logging.getLogger('goblin.shadow').info("Shadow initialized: port[%s], uri[%s]", self.port, self.uri)

    def ok(self):
        if self.shadow_node is not None:
            return self.shadow_node.handler._ok()
        else:
            return False
    
    def stop(self):
        if self.shadow_node is not None:
            self.shadow_node.shutdown('Shadow.stop')
            self.shadow_node = None
