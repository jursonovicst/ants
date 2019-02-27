from multiprocessing import Process
from multiprocessing.connection import Client
from killthebeast import Msg, Egg
from threading import Event
import sched, time


class Nest(Process):
    def __init__(self, address, port=None, name='default'):
        super().__init__(name=name)
        self._conn = Client(address=address if port is None else (address, port), family='AF_UNIX' if port is None else 'AF_INET')

        self._stopevent = Event()

        self._scheduler = sched.scheduler(time.time, time.sleep)
        self.start()

    def run(self):
        self._log("started")
        while not self._stopevent.isSet():
            o = self._conn.recv()

            if o.__class__.__name__ == 'Egg':
                self._scheduler.enter(delay=o.at, priority=1, action=o.hatch)
                self._log("egg with larv '%s' to hatch at %.2f" % (o.larv, o.at))
            elif o.__class__.__name__ == 'Cmd':
                if o.iskick():
                    self._scheduler.run()
                elif o.isterminate():
                    self._stopevent.set()
                    #TODO: terminate running ants as well.
            else:
                self._log("unknown message: '%s'" % o)


        self._log("exits")

    def _log(self, msg):
        self._conn.send(Msg("%s '%s': %s" % (self.__class__.__name__, self.name, msg)))
