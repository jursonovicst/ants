from killthebeast import Ant
import time
from typing import Type

class Egg(object):
    def __init__(self, at:float, larv:Type, **kwargs):
        assert at >= 0, "Egg cannot hatch in the past: %f" % at
        assert larv.__class__.__name__==Ant.__class__.__name__, "Only Ant can hatch from an egg: %s" % larv

        self._at = at
        self._larv = larv
        self._kwargs = kwargs

    @property
    def at(self):
        return self._at

    @property
    def larv(self):
        return self._larv

    def hatch(self):
        print("%s hatched at %f" % (self.__class__.__name__, time.time()))
        ant = self._larv(**self._kwargs)
        ant.start()
        return ant

    def __str__(self):
        return "%s at %.2f with '%s' larv" % (self.__class__.__name__, self._at, self._larv.__name__)