from unittest import TestCase
import http.server
from ants import HTTPAnt, Msg
from multiprocessing.connection import Pipe
from threading import Timer
import random


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<html><body><h1>hi!</h1></body></html>")

#    def log_request(self, code='-', size='-'):
#        pass


class TestHTTPAnt(TestCase):
    def setUp(self):
        self._port = random.randint(20000, 60000)
        self._handler = MyHandler
        self._httpd = http.server.HTTPServer(("", self._port), self._handler)

        # create a connection pair for testing (cheat a little bit, use a pipe instead of an IP connection)
        self._local, self._remote = Pipe()

    def tearDown(self) -> None:
        self._remote.close()
        self._local.close()

        self._httpd.server_close()

    def test_create(self):
        paths = ['/test01.html', '/test02.html']
        delays = [1, 2]

        testant = HTTPAnt("127.0.0.1:%d" % self._port, paths, delays, name='testant')
        testant.conn = self._remote

        # schedule httpd shutdown
        timer = Timer(max(delays) + 0.1, self._httpd.shutdown)
        timer.start()

        # start ant
        testant.start()

        # start httpd, timer will interrupt serving
        self._httpd.serve_forever()

        # thread should be dead
        self.assertFalse(testant.isAlive(), "Ant's thread has not finished within 1 second.")

        # there should be four messages: born, HTTP access, and died
        self.assertTrue(self._local.poll(1), 'Ant has not sent a first (born) message within 1 second.')
        msg = self._local.recv()
        self.assertRegex(str(msg), r"testant.*born", "'%s" % msg)

        self.assertTrue(self._local.poll(1), '')
        msg = self._local.recv()
        self.assertRegex(str(msg), "%s.*: 200" % paths[0], "%s" % msg)

        self.assertTrue(self._local.poll(1), '')
        msg = self._local.recv()
        self.assertRegex(str(msg), "%s.*: 200" % paths[1], "%s" % msg)

        self.assertTrue(self._local.poll(1), 'Ant has not sent a first (born) message within 1 second.')
        msg = self._local.recv()
        self.assertRegex(str(msg), r"testant.*died", "'%s" % msg)

        # there should not be any more messages
        self.assertFalse(self._local.poll(), "Ant sent more than 2 messages: 2nd: '%s'." % msg)
