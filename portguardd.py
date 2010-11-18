#!/usr/bin/env python
# Author: Chris Eberle <eberle1080@gmail.com>

import os, sys, time, getopt
import signal
import resource

from daemon import Daemon

class PortGuard(Daemon):
    def run(self):
        time.sleep(20)
        fh = open('/tmp/test.txt', 'w')
        fh.write('This is a test')
        fh.close()

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
