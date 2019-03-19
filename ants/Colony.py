from ants import Egg, Cmd, Msg
from threading import Thread, Event
from multiprocessing.connection import Listener, wait, Client


class Colony(Thread):

    def __init__(self, address: str, port: int):
        super(Colony, self).__init__(name='Colony')

        self._conns = []
        self._connptr = 0

        self._stopevent = Event()
        self._address = address
        self._port = port

        self._listenerthread = Thread(target=self._listen, args=(self._address, self._port))
        self._listenerthread.start()

        self.start()

    def _listen(self, address: str, port: int):
        try:
            with Listener(address=(address, port)) as listener:
                self._log("listening on %s" % (address if port is None else ("%s:%d" % (address, port))))

                while not self._stopevent.isSet():
                    conn = listener.accept()
                    self._conns.append(conn)

                    if not self._stopevent.isSet():
                        self._log("connection accepted from %s:%d" % listener.last_accepted)

        except KeyboardInterrupt:
            self._log("interrupted")
        except OSError as err:
            self._log(err)

        self._log("stopped listening")

    def run(self):

        while not self._stopevent.isSet():

            if self._conns:
                for conn in wait(self._conns, timeout=0.1):
                    try:
                        msg = conn.recv()
                        if isinstance(msg, Msg):
                            # log message from Nest
                            print(msg)

                    except EOFError:
                        self._log("removes connection")
                        self._conns.remove(conn)
                        if not self._conns:
                            # no more connection
                            self._stopevent.set()

        self._listenerthread.join(5)
        self._log("exited")

    def _sendroundrobbin(self, o):
        if not self._conns:
            raise Exception("No connection to send on!")
        self._conns[self._connptr].send(o)
        self._connptr = (self._connptr + 1) % len(self._conns)

    def _sendtoall(self, o):
        for conn in self._conns:
            conn.send(o)

    def execute(self):
        self._sendtoall(Cmd.kick())

    def terminate(self):
        # send terminate command to all Nests
        self._sendtoall(Cmd.terminate())

        # set terminate event
        self._stopevent.set()

        # Listener is blocked in the accpet() call, open a dummy connection to break blocking
        Client(address=(self._address, self._port), family='AF_INET')

    def addegg(self, egg: Egg):
        self._sendroundrobbin(egg)

    def _log(self, logstring):
        print("%s: %s" % (self.__class__.__name__, logstring))
