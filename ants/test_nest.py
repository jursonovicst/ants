from unittest import TestCase
from ants import Nest, Cmd, Msg, Ant, SleepyAnt, Egg
from multiprocessing.connection import Listener
import random
import time


class TestNest(TestCase):
    def setUp(self):
        self._port = random.randint(30000, 60000)
        self._listener = Listener(address=('127.0.0.1', self._port))

    def tearDown(self) -> None:
        self._listener.close()

    def test_create(self):
        testnest = Nest(address='127.0.0.1', port=self._port, loglevel=Nest.DEBUG, name='testnest')

        # check nest's process
        self.assertEqual(testnest.name, 'testnest')
        self.assertTrue(testnest.is_alive(), "Nest's process should be alive.")

        # check connection
        conn = self._listener.accept()

        # first message should be the created message
        self.assertTrue(conn.poll(0.1), 'Nest has not sent a first (started) message within 0.1s.')
        msg = conn.recv()
        self.assertIsInstance(msg, Msg)
        self.assertRegex(str(msg), r"testnest.*started", "Thread has not started: %s" % msg)

        # check ping command
        conn.send(Cmd.ping())
        msg = conn.recv()
        self.assertIsInstance(msg, Cmd, "Thread should reply with a pong, got '%s'" % type(msg))
        self.assertTrue(msg.ispong(), "Thread should reply with a pong, got '%s'" % msg)

        # terminate nest, should be fast
        testnest.terminate()

        # process should be dead
        testnest.join(0.1)
        self.assertFalse(testnest.is_alive(), "Nest should be dead after 0.1s of its termination.")

        self.assertTrue(conn.poll(0.1), 'Nest has not sent the last (terminated) message within 0.1s.')
        msg = conn.recv()
        self.assertIsInstance(msg, Msg)
        self.assertRegex(str(msg), r"testnest.*terminated", "Thread has not terminated: %s" % msg)

        # do not check log messages...
        conn.close()

    def test_ants(self):
        testnest = Nest(address='127.0.0.1', port=self._port, loglevel=Nest.DEBUG, name='testnest')

        # check connection
        conn = self._listener.accept()

        # first message should be the created message
        self.assertTrue(conn.poll(0.1), 'Nest has not sent a first (started) message within 0.1s.')
        msg = conn.recv()
        self.assertIsInstance(msg, Msg)
        self.assertRegex(str(msg), r"testnest.*started", "Thread has not started: %s" % msg)

        # add egg with sleepyant
        sleepperiod = random.randint(2000, 10000) / 1000
        egg = Egg(delay=1, larv=SleepyAnt, sleepperiod=sleepperiod, name='sleepyant')
        conn.send(egg)

        # check egg placement, should be instantaneous
        self.assertTrue(conn.poll(0.1), '__')
        msg = conn.recv()
        self.assertRegex(str(msg), r"testnest.*hatch", "Egg not layed in nest: %s" % msg)

        # kick nest
        conn.send(Cmd.execute())

        # check ant creation messages, ant should born after 1 sec
        self.assertFalse(conn.poll(0.9), 'Ant born too early')
        self.assertTrue(conn.poll(0.2), 'Ant has not born in 1.1s.')
        msg = conn.recv()
        self.assertRegex(str(msg), r"sleepyant.*born", "Ant has not born yet: %s" % msg)

        # ant waken message must be there, TODO: why is this so slow, why we need to wait an extra second?
        self.assertTrue(conn.poll(sleepperiod + 1), "Ant's waken message hasn't received in %fs." % (sleepperiod + 1))
        msg = conn.recv()
        self.assertRegex(str(msg), r"sleepyant.*died", "Ant has not died yet: %s" % msg)

        # confirm terminate
        self.assertTrue(conn.poll(0.1), 'Command confirmation has not received in 0.1s.')
        msg = conn.recv()
        self.assertIsInstance(msg, Msg)
        self.assertRegex(str(msg), r"testnest.*terminated", "Thread has not started: %s" % msg)

        # process should be dead
        self.assertFalse(testnest.is_alive(), "Nest should be dead after termination.")

        conn.close()

    def test_terminate(self):
        self.skipTest("Termination is not working yet, the scheuler in Nest must be rewriten to allow interrupt.")

        testnest = Nest(address='127.0.0.1', port=self._port, loglevel=Nest.DEBUG, name='testnest')

        # check connection and read first message
        conn = self._listener.accept()
        self.assertTrue(conn.poll(0.1), 'Nest has not sent a first (created) message within 0.1s.')
        conn.recv()

        # add egg with sleepyant
        sleepperiod = random.randint(2000, 10000) / 1000
        egg = Egg(delay=1, larv=SleepyAnt, sleepperiod=sleepperiod, name='sleepyant')
        conn.send(egg)

        # check egg placement, should be instantaneous
        self.assertTrue(conn.poll(0.1), '__')
        msg = conn.recv()
        self.assertRegex(str(msg), r"testnest.*hatch", "Egg not layed in nest: %s" % msg)

        # kick nest
        conn.send(Cmd.execute())

        # check ant creation messages
        self.assertTrue(conn.poll(1.1), '__')
        msg = conn.recv()
        self.assertRegex(str(msg), r"sleepyant.*born", "Ant has not born yet: %s" % msg)

        # wait a bit, then terminate
        time.sleep(random.randint(1000, sleepperiod * 1000 - 1000) / 1000)
        conn.send(Cmd.terminate())

        # ant died message must be there
        self.assertTrue(conn.poll(0.1), "Ant's died message hasn't received in 0.1s.")
        msg = conn.recv()
        self.assertRegex(str(msg), r"sleepyant.*died", "Ant has not died yet: %s" % msg)

        # confirm terminate
        self.assertTrue(conn.poll(0.1), 'Command confirmation has not received in 0.1s.')
        msg = conn.recv()
        self.assertIsInstance(msg, Cmd)
        self.assertTrue(msg.isterminated())

        # check if nest terminates
        testnest.join(0.1)

        # process should be dead
        self.assertFalse(testnest.is_alive(), "Nest should be dead after termination.")

        conn.close()
