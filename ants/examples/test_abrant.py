from unittest import TestCase
from ants import ABRAnt
from multiprocessing.connection import Pipe


class TestABRAnt(TestCase):
    def setUp(self):
        # create a connection pair for testing (cheat a little bit, use a pipe instead of an IP connection)
        self._local, self._remote = Pipe()

    def tearDown(self) -> None:
        self._remote.close()
        self._local.close()

    def test_create(self):
        host = "playready.directtaps.net"
        path = "/smoothstreaming/TTLSS720VC1/To_The_Limit_720.ism/Manifest"
        testant = ABRAnt(server=host,
                         manifestpath=path,
                         strategy=min,
                         duration=30,
                         loglevel=ABRAnt.DEBUG,
                         name="smoothstreamant")
        testant.conn = self._remote
        testant.start()

        # there should be born message
        self.assertTrue(self._local.poll(0.1), 'Ant has not sent a born message.')
        msg = self._local.recv()
        self.assertRegex(str(msg), r"smoothstreamant.*born", "%s" % msg)

        # then only HTTP 200 OK
        for i in range(0, 30):
            msg = self._local.recv()
            self.assertRegex(str(msg), r"smoothstreamant.*http://%s.*Fragments.*200" % host, "%s" % msg)

        # died message
        self.assertTrue(self._local.poll(0.1), 'Ant has not sent a died message.')
        msg = self._local.recv()
        self.assertRegex(str(msg), r"smoothstreamant.*died", "%s" % msg)

        # there should not be any more messages
        self.assertFalse(self._local.poll(), "Ant sent unexpected messages: '%s'." % msg)
