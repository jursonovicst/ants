class Msg(object):

    def __init__(self, msg: str):
        self._msg = msg

    def __str__(self):
        return self._msg


class Cmd(object):
    _EXECUTE = 0
    _TERMINATE = 1
    _TERMINATED = 2
    _PING = 3
    _PONG = 4

    def __init__(self, command):
        self._command = command

    def __str__(self):
        if self._command == self._EXECUTE:
            return "EXECUTE"
        elif self._command == self._TERMINATE:
            return "TERMINATE"
        elif self._command == self._TERMINATED:
            return "TERMINATED"
        elif self._command == self._PING:
            return "PING"
        elif self._command == self._PONG:
            return "PONG"
        else:
            assert False, "Unknown command type: %d" % self._command

    @classmethod
    def execute(cls):
        return cls(cls._EXECUTE)

    def isexecute(self):
        return self._command == self._EXECUTE

    @classmethod
    def terminate(cls):
        return cls(cls._TERMINATE)

    def isterminate(self):
        return self._command == self._TERMINATE

    @classmethod
    def terminated(cls):
        return cls(cls._TERMINATED)

    def isterminated(self):
        return self._command == self._TERMINATED

    @classmethod
    def ping(cls):
        return cls(cls._PING)

    def isping(self):
        return self._command == self._PING

    @classmethod
    def pong(cls):
        return cls(cls._PONG)

    def ispong(self):
        return self._command == self._PONG
