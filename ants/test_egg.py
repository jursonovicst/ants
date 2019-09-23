from unittest import TestCase
from ants import Egg, Ant
import random
from multiprocessing.connection import Pipe


class TestEgg(TestCase):

    def setUp(self):
        # create a connection pair for testing (cheat a little bit, use a pipe instead of an IP connection)
        self._local, self._remote = Pipe()

        # random test parameters
        self._delay = random.randint(0, 5000) / 1000

    def tearDown(self) -> None:
        # cleanup
        self._remote.close()
        self._local.close()

    def test_create(self):
        myegg = Egg(delay=self._delay, larv=Ant, name='testant')

        self.assertEqual(myegg.delay, self._delay)
        self.assertEqual(myegg.larv, Ant)

    def test_create_past(self):
        self.assertRaises(ValueError, Egg, delay=-1 * self._delay, larv=Ant, name='testant')

    def test_hatch(self):
        # create egg with an Ant ant
        myegg = Egg(delay=self._delay, larv=Ant, name='testant')

        # dummy class to capture ant
        class Nest:
            def __init__(self):
                self.ant = None

            def addant(self, ant):
                self.ant = ant

        dummynest = Nest()

        # hatch egg
        myegg.hatch(dummynest, self._remote)

        # check hatched ant
        self.assertIsInstance(dummynest.ant, Ant)
        self.assertEqual(dummynest.ant.name, 'testant')

        # there should not be any message
        self.assertFalse(self._local.poll(), "There should not be any message, got at least one")
