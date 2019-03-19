from ants import Msg, Ant
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

    def __init__(self, address: str, port: int, name='default'):
        super(Nest, self).__init__(name=name)
        try:
            self._conn = Client(address=(address, port), family='AF_INET')

            self._stopevent = Event()
            self._ants = []

            self._scheduler = sched.scheduler(time.time, time.sleep)
            self.start()

        except ConnectionRefusedError as err:
            print("Cannot connect to Colony: '%s'" % err)
            sys.exit(1)
        except Exception as e:
            self._log(e)

    def addant(self, ant: Ant):
        # assert isinstance(ant, Ant), "Only ants can be added to nest, I got '%s'" % type(ant) TODO: fix

        # set conn for logging
        ant.conn = self._conn

        self._ants.append(ant)
        ant.start()

    def run(self):
        self._log("started, max open files: '%d %d'" % resource.getrlimit(resource.RLIMIT_NOFILE))
        while not self._stopevent.isSet():
            try:
                o = self._conn.recv()

                if o.__class__.__name__ == 'Egg':
                    self._scheduler.enter(delay=o.at, priority=1, action=o.hatch, argument=(self,))
                    self._log("egg with larv '%s' to hatch at %.2f" % (o.larv, o.at))
                elif o.__class__.__name__ == 'Cmd':
                    if o.iskick():
                        self._scheduler.run()
                    elif o.isterminate():
                        self._stopevent.set()
                        # TODO: terminate running ants as well.
                else:
                    self._log("unknown message: '%s'" % o)

            except KeyboardInterrupt:
                self._stopevent.set()

        self._log("exited")
        self._conn.close()
        sys.exit(0)

    def _log(self, msg):
        self._conn.send(Msg("%s '%s': %s" % (self.__class__.__name__, self.name, msg)))
