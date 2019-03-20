from ants import Nest
from typing import Type
from ants import Msg
from multiprocessing.connection import Connection


class Egg(object):
    def __init__(self, delay: float, larv: Type, **kwargs):
        """
        An Egg is used to encapsulate an Ant and schedule its birth. Eggs lay in a Nest, and after 'delay' seconds,
        they hatch, and an Ant is born.

        :param delay: Duration, after which the egg will hatch, and an Ant will born.
        :param larv: The type (and not an instance) of the Ant to be born.
        :param kwargs: Custom arguments passed to the Ant's constructor at birth.
        """
        assert delay >= 0, "An Egg cannot hatch in the past: %f" % delay

        self._delay = delay
        self._larv = larv
        self._kwargs = kwargs

    @property
    def delay(self):
        return self._delay

    @property
    def larv(self):
        return self._larv

    def hatch(self, nest: Nest, conn: Connection):
        """
        If an Egg reaches its hatch time, an Ant (with type of self._larv) will born. This method is called by the
        Nest's Scheduler, so it needs to catch all errors and implement logging by itself.

        :param nest: The nest instance, in which the egg hatched.
        :param conn: Connection used for remote logging.
        """
        # create Ant and add to its Nest, Nest will start it...
        try:
            ant = self._larv(**self._kwargs)
            nest.addant(ant)
        except Exception as e:
            self._log(e, conn)

    def _log(self, logstring, conn: Connection):
        """
        Use remote logging on Colony.
        """
        conn.send(Msg("%s '%s': %s" % (
            self.__class__.__name__, self._kwargs['name'] if 'name' in self._kwargs else 'noname',
            logstring)))
