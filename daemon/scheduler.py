# Heavily based on:
# http://packages.python.org/APScheduler/

from threading import Thread, Event, Lock
from datetime import datetime, timedelta
from time import mktime

class Scheduler(object):
    """
    A simple scheduler. Executes a job once at a predefined time.
    """

    stopped = False
    thread = None

    def __init__(self):
        """
        Construct a new scheduler
        """

        self.jobs =[]
        self.jobs_lock = Lock()
        self.wakeup = Event()

    def start(self):
        """
        Start the scheduler up
        """

        if self.thread and self.thread.isAlive():
            return

        self.stopped = False
        self.thread = Thread(target = self.run, name = 'Scheduler')
        self.thread.setDaemon(True)
        self.thread.start()

    def stop(self):
        """
        Stop the scheduler
        """

        if self.stopped or not self.thread.isAlive():
            return

        self.stopped = True
        self.wakeup.set()
        self.thread.join(5)
        self.jobs = []

    def add_job(self, date, func, args = None):
        """
        Add a new job to the scheduler
        """

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
        """
        Retrieve the time of the next-to-be-executed task
        """

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
        """
        Get the difference between two datetimes
        """

        later = mktime(date1.timetuple())
        earlier = mktime(date2.timetuple())
        return int(later - earlier)

    def _get_current_jobs(self):
        """
        Get a list of jobs whose times have lapsed
        """

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
        """
        The main scheduler loops
        """

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

