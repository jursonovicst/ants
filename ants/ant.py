from threading import Thread, Event
import sched
import time
from ants import Msg
import random  # this is needed, because the strategy function may be a random function.


class Ant(Thread):
    """
    An ant template, use it to create your own ant.
    """

    def __init__(self, **kw):
        """
        An ant does regular work. You may overload this method to initialize stuff for your Ant.
        :param kw: keyword arguments passed to the Thread class
        """
        super(Ant, self).__init__(**kw)

        # Ant's scheduler to start tasks.
        self._scheduler = sched.scheduler(time.time, time.sleep)

        # connection for remote logging
        self._conn = None

        self._stopevent = Event()

    def schedulework(self, delay, *args):
        """
        Schedule work for the ant.
        :param delay: Time at work should be done
        :param args: Arguments passed to the work() method.
        """
        self._scheduler.enter(delay=delay, priority=100, action=self.work, argument=args)

    def run(self):
        """
        Do not overload this function, overload work() instead.
        """
        self._log("born")

        # process tasks, this will block till the end of simulation or interrupt.
        self._scheduler.run()

        # clean up stuff, if any
        try:
            self.cleanup()
        except BaseException as e:
            self._log("cleanup error: '%s'" % str(e))

        self._log("died")

    def work(self, *args):
        """
        Overload this to define your work.
        :param args: optional arguments for your implementation.
        """
        pass

    def cleanup(self):
        """
        Called after finished processing the tasks to clean up stuff. You may overload this method.
        """
        pass

    def terminate(self):
        self._stopevent.set()

    @property
    def conn(self):
        return self._conn

    @conn.setter
    def conn(self, conn):
        self._conn = conn

    def _log(self, msg):
        assert self._conn is not None, "I need a valid connection to send log messages on..."
        self._conn.send(Msg("%s '%s': %s" % (self.__class__.__name__, self.name, msg)))