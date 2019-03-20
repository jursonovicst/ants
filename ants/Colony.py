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

        # create and start a thread to accept connections from local or remote nests
        self._listenerthread = Thread(target=self._listen, args=(self._address, self._port))
        self._listenerthread.start()

        # start own thread
        self.start()

    def _listen(self, address: str, port: int):
        """
        Listener.accept() blocks, therefore an own thread is needed to encapsulate it.
        :param address: IP address to listen on
        :param port: port
        """
        try:
            with Listener(address=(address, port)) as listener:
                self._log("listening on %s" % (address if port is None else ("%s:%d" % (address, port))))

                while not self._stopevent.isSet():
                    conn = listener.accept()
                    self._conns.append(conn)

                    if not self._stopevent.isSet():
                        self._log("connection accepted from %s:%d" % listener.last_accepted)

        except KeyboardInterrupt:
            pass
        except OSError as err:
            self._log(err)

        self._log("stopped listening")

    def run(self):
        """
        Manage Communication with Nests, do logging.
        """

        while not self._stopevent.isSet():
            for conn in wait(self._conns, timeout=0.1):
                try:
                    o = conn.recv()
                    if isinstance(o, Msg):
                        # log message from Nest
                        print(o)
                    elif isinstance(o, Cmd):
                        if o.isterminated():
                            self._log("Nest %s terminated" % "_")
                            self._conns.remove(conn)
                            conn.close()

                            # terminate, if there are no more Nests
                            if not self._conns:
                                self._log("No more Nest in connection pool, terminating")
                                self.terminate()

                except EOFError:
                    self._log("connection to Nest %s lost" % "_")
                    self._conns.remove(conn)

        # Listener is blocked in the accpet() call, open a dummy connection to break blocking and let it finish
        Client(address=(self._address, self._port), family='AF_INET')
        self._listenerthread.join()

        self._log("exited")

    def _sendroundrobbin(self, o):
        """
        Send object to a Nest chosen on a round robbin fashion.
        """
        if not self._conns:
            raise Exception("No connection to send on!")
        self._conns[self._connptr].send(o)
        self._connptr = (self._connptr + 1) % len(self._conns)

    def _sendtoall(self, o):
        """
        Send object to all Nests.
        """
        for conn in self._conns:
            conn.send(o)

    def _log(self, logstring):
        """
        Print loggstring.
        """
        print("%s: %s" % (self.__class__.__name__, logstring))

    def execute(self):
        """
        Trigger execution, Eggs are going to hatch now.
        """
        self._sendtoall(Cmd.execute())

    def terminate(self):
        """
        Terminate execution.
        """
        self._sendtoall(Cmd.terminate())

        # set own terminate event as well
        self._stopevent.set()

    def addegg(self, egg: Egg):
        """
        Distribute Egg among Nests on a round robbin fashion.
        """
        self._sendroundrobbin(egg)
