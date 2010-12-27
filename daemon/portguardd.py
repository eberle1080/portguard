#!/usr/bin/env python
# Author: Chris Eberle <eberle1080@gmail.com>

import os, sys, time, getopt, signal, resource, datetime, which, subprocess

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from daemon import Daemon
from threading import Thread, Lock
from scheduler import Scheduler

iptables = None
opened_ports = {}
forwarded_ports = {}
open_id = 1
glock = Lock()

def run_iptables(params):
    global iptables, glock
    cmd = [iptables] + params

    glock.acquire()
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        return (proc.returncode, out, err)
    finally:
        glock.release()

def open_port(src_host, dst_port):
    args = ['-s', str(src_host), '-p', 'tcp', '--dport', str(dst_port), '-j', 'ACCEPT']
    r,o,e = run_iptables(['-I', 'portguard', '1'] + args)
    if r != 0:
        return False
    return True

def close_port(src_host, dst_port, iopen_id):
    global glock, opened_ports

    args = ['-s', str(src_host), '-p', 'tcp', '--dport', str(dst_port), '-j', 'ACCEPT']
    r,o,e = run_iptables(['-D', 'portguard'] + args)

    glock.acquire()
    try:
        if opened_ports.has_key(iopen_id):
            del opened_ports[iopen_id]
    finally:
        glock.release()

    if r != 0:
        return False
    return True

def forward_port(src_host, my_port, dst_host, dst_port):
    args = ['-s', str(src_host), '-p', 'tcp', '--dport', str(my_port), '-j', 'DNAT', '--to', str(dst_host) + ':' + str(dst_port)]
    r,o,e = run_iptables(['-t', 'nat', '-I', 'portguard'] + args)
    if r != 0:
        return False
    return True

def close_forward(src_host, my_port, dst_host, dst_port, fopen_id):
    global glock, forwarded_ports

    args = ['-s', str(src_host), '-p', 'tcp', '--dport', str(my_port), '-j', 'DNAT', '--to', str(dst_host) + ':' + str(dst_port)]
    r,o,e = run_iptables(['-t', 'nat', '-D', 'portguard'] + args)

    glock.acquire()
    try:
        if forwarded_ports.has_key(fopen_id):
            del forwarded_ports[fopen_id]
    finally:
        glock.release()

    if r != 0:
        return False
    return True

class PortGuard(object):
    def __init__(self, sched):
        self.sched = sched

    def open(self, user, host, port, timeout):
        global glock, opened_ports, open_id

        if not user or len(user) == 0:
            return -1
        if not host or len(host) == 0:
            return -1
        if not port or port <= 0 or port >= 65535:
            return -1
        if not timeout or timeout <= 0:
            return -1

        future = datetime.datetime.now() + datetime.timedelta(0, timeout)
        if open_port(host, port) != True:
            return -1
        
        glock.acquire()
        try:
            my_openid = open_id
            open_id += 1
            opened_ports[my_openid] = (user, host, port, future)
        finally:
            glock.release()

        self.sched.add_job(future, close_port, [host, port, my_openid])

        return 0

    def forward(self, user, host, port, dstHost, dstPort, timeout):
        global glock, forwarded_ports, open_id

        if not user or len(user) == 0:
            return -1
        if not host or len(host) == 0:
            return -1
        if not port or port <= 0 or port >= 65535:
            return -1
        if not dstHost or len(dstHost) == 0:
            return -1
        if not dstPort or dstPort <= 0 or dstPort >= 65535:
            return -1
        if not timeout or timeout <= 0:
            return -1

        future = datetime.datetime.now() + datetime.timedelta(0, timeout)

        if forward_port(host, port, dstHost, dstPort) != True:
            return -1

        glock.acquire()
        try:
            my_openid = open_id
            open_id += 1
            forwarded_ports[my_openid] = (user, host, port, dstHost, dstPort, future)
        finally:
            glock.release()

        self.sched.add_job(future, close_forward, [host, port, dstHost, dstPort, my_openid])

        return 0

    def list_open(self):
        pass

    def list_forward(self):
        pass

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/pg',)

class PortGuardDaemon(Daemon):
    def run(self):
        self.sched = Scheduler()
        self.server = SimpleXMLRPCServer(("0.0.0.0", 8812),
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
