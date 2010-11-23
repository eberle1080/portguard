# Heavily based on:
# http://packages.python.org/APScheduler/

from threading import Thread, Event, Lock
from datetime import datetime, timedelta
from time import mktime

class Scheduler(object):
    stopped = False
    thread = None

    def __init__(self):
        self.jobs =[]
        self.jobs_lock = Lock()
        self.wakeup = Event()

    def start(self):
        if self.thread and self.thread.isAlive():
            return

        self.stopped = False
        self.thread = Thread(target = self.run, name = 'Scheduler')
        self.thread.setDaemon(True)
        self.thread.start()

    def stop(self):
        if self.stopped or not self.thread.isAlive():
            return

        self.stopped = True
        self.wakeup.set()
        self.thread.join(5)
        self.jobs = []

    def add_job(self, date, func, args = None):
        if self.stopped:
            return False
        if not hasattr(func, '__call__'):
            return False

        if args == None:
            args = []

        self.jobs_lock.acquire()
        try:
            self.jobs.append([date, func, args])
        finally:
            self.jobs_lock.release()

        self.wakeup.set()
        return True

    def _get_next_time(self, now):
        next_wakeup = None
        finished_jobs = []

        self.jobs_lock.acquire()
        try:
            for job in self.jobs:
                next_run = job[0]
                if next_run == None:
                    finished_jobs.append(job)
                elif next_run and (next_wakeup == None or next_run < next_wakeup):
                    next_wakeup = next_run

            for job in finished_jobs:
                self.jobs.remove(job)
        finally:
            self.jobs_lock.release()

        return next_wakeup

    def _time_difference(self, date1, date2):
        later = mktime(date1.timetuple())
        earlier = mktime(date2.timetuple())
        return int(later - earlier)

    def _get_current_jobs(self):
        current_jobs = []
        now = datetime.now()
        start = now - timedelta(seconds = 1)

        self.jobs_lock.acquire()
        try:
            for job in self.jobs:
                next_run = job[0]
                if next_run:
                    time_diff = self._time_difference(now, next_run)
                    if next_run < now and time_diff <= 1:
                        current_jobs.append(job)
        finally:
            self.jobs_lock.release()

        return current_jobs

    def run(self):
        self.wakeup.clear()
        while not self.stopped:
            for job in self._get_current_jobs():
                func = job[1]
                args = job[2]
                func(*args)
                job[0] = None

            now = datetime.now()
            next_wakeup_time = self._get_next_time(now)

            if next_wakeup_time != None:
                wait_seconds = self._time_difference(next_wakeup_time, now)
                self.wakeup.wait(wait_seconds)
            else:
                self.wakeup.wait()
            self.wakeup.clear()

