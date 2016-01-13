"""Command-line handler for Goblin Shadow Master"""

import logging
import os
import sys
import time
import optparse

import rosshadow.shadow
from rosshadow.shadow_api import NUM_WORKERS

def configure_logging():
    """
    Setup filesystem logging for the shadow
    """
    filename = 'shadow.log'
    # #988 __log command-line remapping argument
    import rosgraph.names
    import rosgraph.roslogging
    mappings = rosgraph.names.load_mappings(sys.argv)
    if '__log' in mappings:
        logfilename_remap = mappings['__log']
        filename = os.path.abspath(logfilename_remap)
    _log_filename = rosgraph.roslogging.configure_logging('[Goblin][Shadow]', logging.DEBUG, filename=filename)

def rosshadow_main(argv=sys.argv, stdout=sys.stdout, env=os.environ):
    parser = optparse.OptionParser(usage="usage: zenmaster [options]")
    parser.add_option("--core",
                      dest="core", action="store_true", default=False,
                      help="run as core")
    parser.add_option("-p", "--port", 
                      dest="port", default=0,
                      help="override port", metavar="PORT")
    parser.add_option("-w", "--numworkers",
                      dest="num_workers", default=NUM_WORKERS, type=int,
                      help="override number of worker threads", metavar="NUM_WORKERS")
    parser.add_option("-t", "--timeout",
                      dest="timeout",
                      help="override the socket connection timeout (in seconds).", metavar="TIMEOUT")
    options, args = parser.parse_args(argv[1:])

    # only arg that zenmaster supports is __log remapping of logfilename
    for arg in args:
        if not arg.startswith('__log:='):
            parser.error("unrecognized arg: %s"%arg)
    configure_logging()   
    
    port = rosshadow.shadow.DEFAULT_SHADOW_PORT
    if options.port:
        port = int(options.port)
    logger = logging.getLogger("rosshadow.main")
    logger.info("initialization complete, waiting for shutdown")

    if options.timeout is not None and float(options.timeout) >= 0.0:
        logger.info("Setting socket timeout to %s" % options.timeout)
        import socket
        socket.setdefaulttimeout(float(options.timeout))

    try:
        logger.info("Starting Goblin Shadown Node")
        shadow = rosshadow.shadow.Shadow(port, options.num_workers)
        shadow.start()

        import time
        while shadow.ok():
            time.sleep(.1)
    except KeyboardInterrupt:
        logger.info("keyboard interrupt, will exit")
    finally:
        logger.info("stopping shadow...")
        shadow.stop()

if __name__ == "__main__":
    rosshadow_main()
