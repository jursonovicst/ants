from ants import Msg, Ant, Cmd
from multiprocessing import Process
from multiprocessing.connection import Client
from threading import Event
import sched
import time
import sys
import resource


class Nest(Process):
    """
    Represents a group of ants. It is realised by a Process class. A host run one nest per CPU core by default.
    Use the --nextcount argument to change it.
    """

    def __init__(self, address: str, port: int, name='noname'):
        super(Nest, self).__init__(name=name)
        try:
            # open connection towards the colony
            self._conn = Client(address=(address, port), family='AF_INET')

            self._stopevent = Event()
            self._startevent = Event()
            self._ants = []

            # load simulation Queen
            #            with open("examples/simple.py", "r") as f:
            #                exec(f.read())

            # scheduler used for scheduling  hatch events of Eggs.
            self._scheduler = sched.scheduler(time.time, time.sleep)

            self.start()

        except ConnectionRefusedError as err:
            print("Cannot connect to Colony on %s:%d: '%s', terminating." % (address, port, err))
            sys.exit(1)
        except Exception as e:
            self._log(e)

    def addant(self, ant: Ant):
        """
        Keep track of hatched Ants.
        """
        # assert issubclass(ant, type(Ant)), "Only ants can be added to nest, I got '%s'" % type(ant) #TODO: fix this

        # set Ant's conn for logging
        ant.conn = self._conn

        self._ants.append(ant)
        ant.start()

    def run(self):
        """
        Manage egg hatching, communication with Colony.
        """
        self._log("started, max open files: '%d %d'" % resource.getrlimit(resource.RLIMIT_NOFILE))

        try:
            # keep checking commands till stopevent
            while not self._stopevent.isSet():

                # poll till the next event, or for 0.1 seconds, if not yet executing.
                polltime = self._scheduler.run(blocking=False) if self._startevent.isSet() else 0.1

                # remember the start of pooling. If waiting during polling is interrupted, the remaining time must be
                # polled again.
                pollstart = time.time()

                # terminate, if there are no more eggs to hatch (Scheduler.run() returns None)
                if polltime is None:
                    self._stopevent.set()

                # do polling, repeate with the remaining wait time, if interrupted by a message.
                while not self._stopevent.isSet() and self._conn.poll(timeout=max(0, polltime)):
                    o = self._conn.recv()

                    # if isinstance(o, Egg): #TODO figure out, why this is not working
                    if o.__class__.__name__ == 'Egg':
                        self._scheduler.enter(delay=o.delay, priority=1, action=o.hatch, argument=(self, self._conn,))
                        self._log("egg with larv '%s' to hatch at %.2f" % (o.larv, o.delay))
                    elif isinstance(o, Cmd):
                        if o.isexecute():
                            self._startevent.set()
                        elif o.isterminate():
                            self._terminate()

                    # calculate remaining wait time
                    polltime -= time.time() - pollstart

            # wait for still running ants to finish
            for ant in self._ants:
                if ant.is_alive():
                    ant.join()
                    self._ants.remove(ant)

        except KeyboardInterrupt:
            self._log("interrupted.")

        self._conn.send(Cmd.terminated())
        self._conn.close()
        sys.exit(0)

    def _terminate(self):
        self._stopevent.set()

        # termiante all running ants
        for ant in self._ants:
            if ant.is_alive():
                ant.terminate()

    def _log(self, logstring):
        """
        Use remote logging on Colony.
        """
        self._conn.send(Msg("%s '%s': %s" % (self.__class__.__name__, self.name, logstring)))
