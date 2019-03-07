from ants import Nest
from typing import Type


class Egg(object):
    def __init__(self, at: float, larv: Type, **kwargs):
        assert at >= 0, "Egg cannot hatch in the past: %f" % at
        # TODO: fix this
        # assert larv.__name__ == Ant.__class__.__name__,
        # "Only Ant can hatch from an egg: %s vs. %s" % (larv.__name__, Ant.__name__)

        self._at = at
        self._larv = larv
        self._kwargs = kwargs

    @property
    def at(self):
        return self._at

    @property
    def larv(self):
        return self._larv

    def hatch(self, nest: Nest):
        """

        :param nest: the nest instance, in which the egg hatched.
        :return:
        """
        # create ant and add to its nest, nest will start it...
        try:
            ant = self._larv(**self._kwargs)
            nest.addant(ant)
        except Exception as e:
            print(e)

    def __str__(self):
        return "%s at %.2f with '%s' larv" % (self.__class__.__name__, self._at, self._larv.__name__)