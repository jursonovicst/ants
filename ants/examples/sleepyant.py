from ants import Ant


class SleepyAnt(Ant):
    """
    An example Ant implementation for sleeping a bit.
    """

    def __init__(self, sleepperiod: int, **kw):
        super(SleepyAnt, self).__init__(**kw)
        if sleepperiod < 0:
            raise ValueError("sleep period must be non negative: %d" % sleepperiod)

        self.schedulework(sleepperiod, sleepperiod)

    def work(self, *args):
        self._log("waken up after %d seconds." % args[0])
