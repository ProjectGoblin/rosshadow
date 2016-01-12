"""
Gobline Shadow
"""

import logging
import time

import rosgraph.xmlrpc

import rosshadow.master_api

from rosmaster.master import DEFAULT_MASTER_PORT
DEFAULT_SHADOW_PORT=11411 #default port for master's to bind to

class Master(object):
    
    def __init__(self,
                 port=DEFAULT_SHADOW_PORT,
                 num_workers=rosshadow.master_api.NUM_WORKERS):
        self.port = port
        self.num_workers = num_workers
        
    def start(self):
        """
        Start the Goblin Shadow.
        """
        self.handler = None
        self.master_node = None
        self.uri = None

        handler = rosshadow.master_api.GoblinShadowHandler(self.num_workers)
        master_node = rosgraph.xmlrpc.XmlRpcNode(self.port, handler)
        master_node.start()

        # poll for initialization
        while not master_node.uri:
            time.sleep(0.0001) 

        # save fields
        self.handler = handler
        self.master_node = master_node
        self.uri = master_node.uri
        
        logging.getLogger('shadow.master').info("Master initialized: port[%s], uri[%s]", self.port, self.uri)

    def ok(self):
        if self.master_node is not None:
            return self.master_node.handler._ok()
        else:
            return False
    
    def stop(self):
        if self.master_node is not None:
            self.master_node.shutdown('Master.stop')
            self.master_node = None
