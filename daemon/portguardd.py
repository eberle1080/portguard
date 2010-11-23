#!/usr/bin/env python
# Author: Chris Eberle <eberle1080@gmail.com>

import os, sys, time, getopt, signal, resource, datetime

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from daemon import Daemon
from threading import Thread
from scheduler import Scheduler

class PortGuard(object):
    def __init__(self, sched):
        self.sched = sched

    def open(self, user, host, port, timeout):
        fh = open('/tmp/portguard.txt', 'w')
        fh.write('Host %s (%s) wants to open port %d for %d seconds\n' % (host, user, port, timeout))
        fh.close()

    def forward(self, user, host, port, dstHost, dstPort, timeout):
        fh = open('/tmp/portguard.txt', 'w')
        fh.write('Host %s (%s) wants to forward port %d to %s:%d for %d seconds\n' % (host, user, port, dstHost, dstPort, timeout))
        fh.close()

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/pg',)

def test(str, sched):
    if str == 'test 1':
        a = datetime.datetime.now() + datetime.timedelta(0, 3)
        sched.add_job(a, test, ['test 3', sched])
    print str

class PortGuardDaemon(Daemon):
    def run(self):
        sched = Scheduler()
        self.server = SimpleXMLRPCServer(("localhost", 8000),
            requestHandler=RequestHandler)
        self.server.register_instance(PortGuard(sched))

        a = datetime.datetime.now() + datetime.timedelta(0, 10)
        b = datetime.datetime.now() + datetime.timedelta(0, 20)
        sched.add_job(a, test, ['test 1', sched])
        sched.add_job(b, test, ['test 2', sched])

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
