#!/usr/bin/env python
# Author: Chris Eberle <eberle1080@gmail.com>

import os, sys, time, getopt, signal, resource, datetime, which, subprocess

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from daemon import Daemon
from threading import Thread
from scheduler import Scheduler

iptables = None

def run_iptables(params):
    global iptables
    cmd = [iptables] + params

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    now = datetime.datetime.now()
    fh = open('/tmp/portguard.txt', 'a+')
    fh.write(str(now) + ': ' + ' '.join(cmd) + ' [' + str(proc.returncode) + ']\n')
    fh.close()

    return (proc.returncode, out, err)

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

        fh = open('/tmp/portguard.txt', 'a+')
        fh.write('Host %s (%s) wants to open port %d for %d seconds\n' % (host, user, port, timeout))
        fh.close()

        args = ['-s', str(host), '-p', 'tcp', '--dport', str(port), '-j', 'ACCEPT']
        r,o,e = run_iptables(['-I', 'portguard', '1'] + args)
        if r != 0:
            return -2

        args = ['-D', 'portguard'] + args
        self.sched.add_job(future, run_iptables, [args])

        return 0

    def forward(self, user, host, port, dstHost, dstPort, timeout):
        fh = open('/tmp/portguard.txt', 'a+')
        fh.write('Host %s (%s) wants to forward port %d to %s:%d for %d seconds\n' % (host, user, port, dstHost, dstPort, timeout))
        fh.close()

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/pg',)

class PortGuardDaemon(Daemon):
    def run(self):
        self.sched = Scheduler()
        self.server = SimpleXMLRPCServer(("0.0.0.0", 8000),
            requestHandler=RequestHandler)
        self.server.register_instance(PortGuard(self.sched))

        self.sched.start()
        try:
            self.server.serve_forever()
        finally:
            self.sched.stop()

if __name__ == "__main__":
    daemon = PortGuardDaemon('/tmp/portguardd.pid')
    if len(sys.argv) == 2:
        try:
            iptables = which.which('iptables')
        except IOError, e:
            print "Unable to locate iptables!"
            sys.exit(1)

        ret =  run_iptables(['-F', 'portguard'])[0]
        ret += run_iptables(['-A', 'portguard', '-j', 'RETURN'])[0]
        ret += run_iptables(['-t', 'nat', '-F', 'portguard'])[0]
        ret += run_iptables(['-t', 'nat', '-A', 'portguard', '-j', 'RETURN'])[0]
        if ret != 0:
            print "Failed to clear the portguard chain, can't continue."
            sys.exit(1)

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
