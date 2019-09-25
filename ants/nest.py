from ants import Msg, Ant, Cmd
from multiprocessing import Process
from multiprocessing.connection import Client, wait
from threading import Event
import sched
import time
import sys
import resource
import signal


class Nest(Process):
    """
    Represents a group of ants. It is realised by a Process class. A host run one nest per CPU core by default.
    Use the --nextcount argument to change it.
    """

    DEBUG = Ant.DEBUG
    INFO = Ant.INFO
    WARNING = Ant.WARNING
    ERROR = Ant.ERROR
    LOGLEVELS = Ant.LOGLEVELS

    _nests = []

    @classmethod
    def _register(cls, nest):
        """
        Keep track of Nest's running processes.
        :param nest:
        :return:
        """
        cls._nests.append(nest)

    @classmethod
    def waitforall(cls):
        """
        Wait for all nests to finish, then remove them from registry.
        """
        try:
            terminatedsentinels = []
            if cls._nests:
                terminatedsentinels = wait(map(lambda n: n.sentinel, cls._nests))

            while cls._nests and terminatedsentinels:
                for nest in [nest for nest in cls._nests if nest.sentinel in terminatedsentinels]:
                    assert not nest.is_alive(), "'%s' nest's sentinel become active, however the nest is still alive" % nest.name
                    cls._nests.remove(nest)

                # call wait only, if there are still nests. wait([]) will wait forever :( Bug?!
                if cls._nests:
                    terminatedsentinels = wait(map(lambda n: n.sentinel, cls._nests))
        except KeyboardInterrupt:
            pass

    @classmethod
    def terminateall(cls):
        """
        Terminate all Nests, do not wait for them.
        """
        for n in cls._nests:
            n.terminate()

    def __init__(self, address: str, port: int, loglevel: int = INFO, name=None):
        super(Nest, self).__init__(name=name)

        try:
            self._stopevent = Event()
            self._startevent = Event()
            self._ants = []
            self._loglevel = loglevel

            # register SIGTERM and SIGINT for graceful exit
            signal.signal(signal.SIGTERM, self._stop)
            signal.signal(signal.SIGINT, self._stop)

            # open connection towards the colony
            self._conn = Client(address=(address, port), family='AF_INET')

            # scheduler used for scheduling hatch events of Eggs.
            self._scheduler = sched.scheduler(time.time, time.sleep)

            # start nest's process
            self.start()

            # register itself
            Nest._register(self)

        except ConnectionRefusedError as err:
            raise SystemError("Cannot connect to Colony on %s:%d: '%s', terminating." % (address, port, err))
        except Exception as e:
            self._logerror(e)

    def _stop(self, signum, frame):
        assert signum == signal.SIGTERM or signum == signal.SIGINT, "Unexpected signal received: %d" % signum
        self._stopevent.set()

    @property
    def loglevel(self) -> int:
        return self._loglevel

    def addant(self, ant: Ant):
        """
        Do not use this function, the Egg will call it, if hatches. Keep track of hatched Ants.
        """
        # assert issubclass(ant, type(Ant)), "Only ants can be added to nest, I got '%s'" % type(ant) #TODO: fix this

        # set Ant's conn for logging
        ant.conn = self._conn

        self._ants.append(ant)
        ant.start()

    def run(self):
        """
        Manage egg hatching, communication with Colony. It must terminate itself, it here are no more events.
        """
        self._log("started, max open files: '%d %d'" % resource.getrlimit(resource.RLIMIT_NOFILE))

        try:
            # terminate if there are no more eggs to hatch (scheduler is empty)
            while not self._stopevent.isSet():

                # remember the start of pooling. If waiting is interrupted, the remaining time must be polled again.
                pollstart = time.time()

                # poll 0.05s if not started yet, or the interval till next event.
                pollintervall = 0.05 if not self._startevent.isSet() else self._scheduler.run(blocking=False)

                # exit if there are no more eggs to hatch
                if pollintervall is None:
                    self._stopevent.set()

                # use blocking poll for sleeping, repeate with the remaining time, if interrupted by a message.
                # Read all messages
                while not self._stopevent.isSet() and self._conn.poll(timeout=max(0, pollintervall)):

                    # (at least one) message received
                    o = self._conn.recv()

                    # if isinstance(o, Egg): #TODO figure out, why this is not working
                    if o.__class__.__name__ == 'Egg':
                        self._scheduler.enter(delay=o.delay, priority=1, action=o.hatch, argument=(self, self._conn,))
                        self._log("egg with larv '%s' to hatch at %.2f" % (o.larv, o.delay))
                    elif isinstance(o, Cmd):
                        if o.isexecute():
                            self._startevent.set()
                        elif o.isping():
                            self._conn.send(Cmd.pong())

                    # calculate remaining wait time
                    pollintervall -= time.time() - pollstart
        except Exception as e:
            self._logerror(e)

        # terminate ants (if alive)
        for ant in self._ants:
            if ant.is_alive():
                ant.terminate()

        # wait for ants to finish
        for ant in self._ants:
            if ant.is_alive():
                ant.join()
            self._ants.remove(ant)

        self._log("terminated.")
        self._conn.close()

        sys.exit(0)

    def _log(self, text, loglevel=INFO):
        """
        Use remote logging on Colony.
        :param text: message to log
        """
        assert self._conn is not None, "I need a valid connection to send log messages on..."

        if loglevel >= self._loglevel:
            self._conn.send(Msg("%s '%s': %s" % (self.__class__.__name__, self.name, text)))

    def _logdebug(self, text):
        self._log(text, Nest.DEBUG)

    def _logwarning(self, text):
        self._log(text, Nest.WARNING)

    def _logerror(self, text):
        self._log(text, Nest.ERROR)
