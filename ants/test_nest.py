from unittest import TestCase
from ants import Nest, Cmd, Msg, Ant
from multiprocessing.connection import Listener


class TestNest(TestCase):
    def test_create(self):
        with Listener(address=('127.0.0.1', 7654)) as listener:
            testnest = Nest(address='127.0.0.1', port=7654, name='testnest')

            # check nest's process
            self.assertEqual(testnest.name, 'testnest')
            self.assertTrue(testnest.is_alive(), "Nest's process should be alive.")

            # check connection
            conn = listener.accept()

            # first message should be the created message
            self.assertTrue(conn.poll(1), 'Nest has not sent a first (created) message within 1 second.')
            msg = conn.recv()
            self.assertIsInstance(msg, Msg)

            conn.send(Cmd.ping())
            msg = conn.recv()
            self.assertIsInstance(msg, Cmd, "Thread should reply with a command, got '%s'" % type(msg))
            self.assertTrue(msg.ispong(), "Thread should reply with a pong, got '%s'" % msg)

            # terminate nest
            conn.send(Cmd.terminate())
            testnest.join(1)

            # last message should be a terminated message
            self.assertTrue(conn.poll(1), 'Nest has not sent the last (terminated) command within 1 second.')
            msg = conn.recv()
            self.assertIsInstance(msg, Cmd)
            self.assertTrue(msg.isterminated())

            # process should be dead
            self.assertFalse(testnest.is_alive())

            # there should not be any message
            self.assertFalse(conn.poll(), "There should not be any message, got at least one")

            conn.close()

    def test_addant(self):
        with Listener(address=('127.0.0.1', 7653)) as listener:
            testnest = Nest(address='127.0.0.1', port=7653, name='testnest')

            # check connection and read first message
            conn = listener.accept()
            self.assertTrue(conn.poll(1), 'Nest has not sent a first (created) message within 1 second.')
            conn.recv()

            # add ant
            testnest.addant(Ant(name='testant'))

            # check ant creation messages
            self.assertTrue(conn.poll(1), '__')
            msg = conn.recv()
            self.assertRegex(str(msg), r"testant.*born", "'%s" % msg)
            self.assertTrue(conn.poll(1), '__')
            msg = conn.recv()
            self.assertRegex(str(msg), r"testant.*died", "'%s" % msg)

            conn.send(Cmd.terminate())
            testnest.join(1)

            conn.close()
