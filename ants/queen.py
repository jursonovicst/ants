from ants import Ant


class Queen(object):
    """
    Define a subclass of Queen and override its layeggs() method to lay eggs.
    """

    def __init__(self, loglevel: int = Ant.INFO):
        self._loglevel = loglevel

    def layeggs(self):
        """
        Override this method to yield Eggs. During initialization, it will be call as many times as it yields Eggs.
        """
        pass
