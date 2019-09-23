from unittest import TestCase
from ants import SleepyAnt
import random
from multiprocessing.connection import Pipe


class TestSleepyAnt(TestCase):
    def setUp(self):
        # create a connection pair for testing (cheat a little bit, use a pipe instead of an IP connection)
        self._local, self._remote = Pipe()

    def tearDown(self) -> None:
        # cleanup
        self._remote.close()
        self._local.close()

    def test_create(self):
        sleepperiod = random.randint(1, 10)
        # create (an empty) ant with name
        testant = SleepyAnt(sleepperiod=sleepperiod, name='sleepyant')

        # set connection for communication
        testant.conn = self._remote

        # start ant
        testant.start()

        # it should be still alive
        testant.join(sleepperiod - 0.1)
        self.assertTrue(testant.isAlive())

        # now, it should be dead
        testant.join(0.2)
        self.assertFalse(testant.isAlive())
