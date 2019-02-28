from threading import Thread, Event  # , Lock
from multiprocessing.connection import Listener, wait
from killthebeast import Egg


class Msg(object):

    def __init__(self, msg: str):
        self._msg = msg

    def __str__(self):
        return self._msg


class Cmd(object):
    _EXECUTE = 0
    _TERMINATE = 1

    def __init__(self, command):
        self._command = command

    @classmethod
    def kick(cls):
        return cls(cls._EXECUTE)

    def iskick(self):
        return self._command == self._EXECUTE

    @classmethod
    def terminate(cls):
        return cls(cls._TERMINATE)

    def isterminate(self):
        return self._command == self._TERMINATE


class Colony(Thread):

    def __init__(self, address: str, port: int):
        super(Colony, self).__init__(name='Colony')

        self._conns = []
        self._connptr = 0
        #        self._connlock = Lock()

        self._stopevent = Event()

        self._listenerthread = Thread(target=self._listen, args=(address, port,))
        self._listenerthread.start()

        self.start()

    def _listen(self, address, port):
        try:
            with Listener(address=(address, port)) as listener:
                self._log("listening on %s" % (address if port is None else ("%s:%d" % (address, port))))

                while not self._stopevent.isSet():
                    conn = listener.accept()
                    self._log("connection accepted from %s:%d" % listener.last_accepted)
                    #                    self._connlock.acquire()
                    self._conns.append(conn)
        #                    self._connlock.release()

        except KeyboardInterrupt:
            print("SSS")
        except OSError as err:
            self._log(err)

        self._log("stopped listening")

    def run(self):
        # self._log("waiting for messages")
        while not self._stopevent.isSet():
            #            self._connlock.acquire()
            if self._conns:
                for conn in wait(self._conns, timeout=0.1):
                    try:
                        msg = conn.recv()
                        print(msg)
                    except EOFError:
                        self._log("removes connection")
                        self._conns.remove(conn)
                        if not self._conns:
                            # no more connection
                            self._stopevent.set()

        #            self._connlock.release()

        self._listenerthread.join(5)
        self._log("exited")

    def _send(self, o):
        assert self._conns, "No connection to send on"
        self._conns[self._connptr].send(o)
        self._connptr = (self._connptr + 1) % len(self._conns)

    def _sendtoall(self, o):
        for conn in self._conns:
            conn.send(o)

    def execute(self):
        self._sendtoall(Cmd.kick())

    def wait(self):
        self._stopevent.wait()

    def terminate(self):
        self._sendtoall(Cmd.terminate())

    def addegg(self, egg: Egg):
        self._send(egg)

    def _log(self, msg):
        print("%s: %s" % (self.__class__.__name__, msg))
