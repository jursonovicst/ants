from ants import Ant
import pycurl


class HTTPAnt(Ant):
    """
    An example Ant implementation for accessing a list of HTTP URLs.
    """

    def __init__(self, server: str, paths, delays, host: str = None, **kw):
        """

        :param server: HTTP server IP address or FQDN to connect to
        :param paths: list of paths to fetch
        :param delays: list of delays (counting from born) to schedule fetch
        :param host: host header to override (optional)
        :param kw: any other parameter to pass to the Ant class
        """
        super(HTTPAnt, self).__init__(**kw)
        if len(paths) != len(delays):
            raise ValueError("length mismatch: %d vs. %d" % (len(paths), len(delays)))

        self._server = server

        self._curl = pycurl.Curl()
        self._curl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        if host is not None:
            self._curl.setopt(pycurl.HTTPHEADER, ['Host: %s' % host])

        # schedule work
        for path, delay in zip(paths, delays):
            self.schedulework(delay, path)

    def work(self, *args):
        path = args[0]
        url = "http://%s%s" % (self._server, path)

        self._curl.setopt(pycurl.URL, url)
        self._curl.perform()

        self._log("'%s': %s" % (url, self._curl.getinfo(pycurl.HTTP_CODE)))

    def cleanup(self):
        self._curl.close()
