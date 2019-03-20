class Msg(object):

    def __init__(self, msg: str):
        self._msg = msg

    def __str__(self):
        return self._msg


class Cmd(object):
    _EXECUTE = 0
    _TERMINATE = 1
    _TERMINATED = 2

    def __init__(self, command):
        self._command = command

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
