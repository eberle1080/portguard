#!/usr/bin/env python
# Author: Chris Eberle <eberle1080@gmail.com>

import os, sys, time, getopt, signal, resource, sched

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from daemon import Daemon
from threading import Thread

class TimeoutThread(Thread):
    def __init__(self, scheduler, lock):
        Thread.__init__(self)
        self.scheduler = scheduler
        self.lock = lock

    def run(self):
        while 1:
            pass

class PortGuard(object):
    def open(self, user, host, port, timeout):
        fh = open('/tmp/portguard.txt', 'w')
        fh.write('Host %s (%s) wants to open port %d for %d seconds\n' % (host, user, port, timeout))
        fh.close()

    def forward(self, user, host, port, dstHost, dstPort, timeout):
        fh = open('/tmp/portguard.txt', 'w')
        fh.write('Host %s (%s) wants to forward port %d to %s:%d for %d\n' % (host, user, port, dstHost, dstPort, timeout))
        fh.close()

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/pg',)

class PortGuardDaemon(Daemon):
    def run(self):
        self.server = SimpleXMLRPCServer(("localhost", 8000),
            requestHandler=RequestHandler)
        self.server.register_instance(PortGuard())
        self.server.serve_forever()

if __name__ == "__main__":
    daemon = PortGuard('/tmp/portguardd.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
    else:
        print "Usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(1)
