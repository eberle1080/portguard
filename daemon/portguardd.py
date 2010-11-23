#!/usr/bin/env python
# Author: Chris Eberle <eberle1080@gmail.com>

import os, sys, time, getopt, signal, resource, datetime

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from daemon import Daemon
from threading import Thread
from scheduler import Scheduler

def test(name):
    print "My name is " + str(name)

class PortGuard(object):
    def __init__(self, sched):
        self.sched = sched

    def open(self, user, host, port, timeout):
        if not user or len(user) == 0:
            return -1
        if not host or len(host) == 0:
            return -1
        if not port or port <= 0 or port >= 65535:
            return -1
        if not timeout or timeout <= 0:
            return -1

        future = datetime.datetime.now() + datetime.timedelta(0, timeout)

        fh = open('/tmp/portguard.txt', 'w')
        fh.write('Host %s (%s) wants to open port %d for %d seconds\n' % (host, user, port, timeout))
        fh.close()

        self.sched.add_job(future, test, [user])

        return 0

    def forward(self, user, host, port, dstHost, dstPort, timeout):
        fh = open('/tmp/portguard.txt', 'w')
        fh.write('Host %s (%s) wants to forward port %d to %s:%d for %d seconds\n' % (host, user, port, dstHost, dstPort, timeout))
        fh.close()

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/pg',)

class PortGuardDaemon(Daemon):
    def run(self):
        sched = Scheduler()
        self.server = SimpleXMLRPCServer(("localhost", 8000),
            requestHandler=RequestHandler)
        self.server.register_instance(PortGuard(sched))

        sched.start()
        try:
            self.server.serve_forever()
        finally:
            sched.stop()

if __name__ == "__main__":
    daemon = PortGuardDaemon('/tmp/portguardd.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'debug' == sys.argv[1]:
            print "Starting daemon in foreground"
            daemon.run()
        else:
            print "Unknown command"
            sys.exit(2)
    else:
        print "Usage: %s start|stop|restart|debug" % sys.argv[0]
        sys.exit(1)
