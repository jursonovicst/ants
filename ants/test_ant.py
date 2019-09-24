from unittest import TestCase
from ants import Ant, Msg
from multiprocessing.connection import Pipe
import time
import random


class TestAnt(TestCase):

    def setUp(self):
        # create a connection pair for testing (cheat a little bit, use a pipe instead of an IP connection)
        self._local, self._remote = Pipe()

    def tearDown(self) -> None:
        # cleanup
        self._remote.close()
        self._local.close()

    def test_create(self):
        # create (an empty) ant with name
        testant = Ant(name='emptyant')
        self.assertEqual(testant.name, 'emptyant',
                         "Ant's thread should have the name 'emptyant', got %s" % testant.name)

        # set connection for communication
        testant.conn = self._remote
        self.assertEqual(testant.conn, self._remote, 'Ant does not have the correct connection.')

        # add some work
        delay = random.randint(2000, 5000) / 1000
        testant.schedulework(delay)

        # start ant
        testant.start()

        # wait till ant finishes (should be very fast)
        testant.join(delay + 0.1)

        # thread should be dead
        self.assertFalse(testant.isAlive(), "Ant's thread has not finished within 0.1 second.")

        # there should be two messages: born and died
        self.assertTrue(self._local.poll(0.1), 'Ant has not sent a first (born) message.')
        msg = self._local.recv()
        self.assertRegex(str(msg), r"emptyant.*born", "%s" % msg)

        self.assertTrue(self._local.poll(0.1), 'Ant has not sent a second (died) message.')
        msg = self._local.recv()
        self.assertRegex(str(msg), r"emptyant.*died", "%s" % msg)

        # there should not be any more messages
        self.assertFalse(self._local.poll(), "Ant sent more than 2 messages: 2nd: '%s'." % msg)

    def test_terminate(self):
        # create ant
        testant = Ant(name='emptyant')
        testant.conn = self._remote

        # add some long work
        testant.schedulework(random.randint(10000, 20000) / 1000)

        # run
        testant.start()

        # wait a bit
        time.sleep(random.randint(1000, 8000) / 1000)

        # terminate
        testant.terminate()

        # wait till ant finishes (should be very fast)
        testant.join(0.1)

        # thread should be dead
        self.assertFalse(testant.isAlive(), "Ant's thread has not finished after termination.")
