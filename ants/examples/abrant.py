from ants import Ant
from typing import Callable
from manifestparser import MParser
import pycurl


class ABRAnt(Ant):
    """
    An Example ABR streaming Ant implementation, it will open an ABR stream, and download streaming fragments.
    """

    def __init__(self, server: str, manifestpath, strategy, duration=0, host: str = None, statuscodes=None, **kw):
        """
        :param server: IP address or host name of the streaming server.
        :param manifestpath: Path of the manifest to open.
        :param strategy: Bitrate switching strategy, the given function shall return one value of the bitrates, which
        will be handed over as a list of integers in the first argument.
        :param duration: Limit streaming by duration sec.
        :param host: HTTP host header to be sent (may be needed, if server is specified by IP address).
        :param statuscodes: List of expected HTTP status codes, defaut is [200].
        :param kw: Any additional parameter to be handed over to its parent class (and eventually to the Thread class).
        """
        assert isinstance(strategy, Callable), "Strategy must be callable: '%s'" % strategy
        super(ABRAnt, self).__init__(**kw)

        self._host = host
        self._statuscodes = statuscodes if statuscodes is not None else [200]

        self._videocurl = pycurl.Curl()
        self._audiocurl = pycurl.Curl()
        self._videocurl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        self._audiocurl.setopt(pycurl.WRITEFUNCTION, lambda x: None)

        if self._host is not None:
            self._videocurl.setopt(pycurl.HTTPHEADER, ['Host: %s' % self._host])
            self._audiocurl.setopt(pycurl.HTTPHEADER, ['Host: %s' % self._host])

        mparser = MParser("http://%s%s" % (server, manifestpath))

        for at, path, ranges in mparser.fragments(MParser.VIDEO, strategy=strategy, duration=duration):
            self.schedulework(at,
                              self._videocurl,
                              server,
                              path,
                              ranges)

        for at, path, ranges in mparser.fragments(MParser.AUDIO, strategy=strategy, duration=duration):
            self.schedulework(at,
                              self._audiocurl,
                              server,
                              path,
                              ranges)

        # manifestcurl = pycurl.Curl()
        #
        # if host is not None:
        #     manifestcurl.setopt(pycurl.HTTPHEADER, ['Host: %s' % host])
        #
        # try:
        #     manifestcurl.setopt(pycurl.URL, "http://%s%s" % (server, manifestpath))
        #     response = BytesIO()
        #     manifestcurl.setopt(pycurl.WRITEDATA, response)
        #     manifestcurl.perform()
        #
        #     if int(manifestcurl.getinfo(pycurl.HTTP_CODE)) != 200:
        #         raise Exception(
        #             "cannot load %s, return code: %d" % (manifestcurl.geturl(), manifestcurl.getinfo(pycurl.HTTP_CODE)))
        #
        #     manifestcurl.close()
        #
        #     # parse XML and fuck Microsoft!
        #     charset = chardet.detect(response.getvalue())['encoding']
        #     manifest = response.getvalue().decode(charset).encode(charset)
        #     root = etree.fromstring(manifest)
        #
        #     # validate manifest
        #     assert root.tag == 'SmoothStreamingMedia', "Invalid root tag: '%s'" % root.tag
        #     assert root.get('MajorVersion') == '2', "Invalid Major version: '%s'" % root.get('MajorVersion')
        #     assert root.get('IsLive', default="false") != "true", "Live manifests are not supported"
        #
        #     # get TimeScale
        #     timescale = root.get('TimeScale', default='10000000')
        #
        #     # get the StreamIndex for video
        #     streamindex = root.find("StreamIndex[@Type='video']")
        #     if streamindex is not None:
        #         # get the video bitrates
        #         bitrates = list(map(lambda element: int(element.get('Bitrate')), streamindex.findall('QualityLevel')))
        #         assert len(bitrates) == int(streamindex.get('QualityLevels')), "invalid bitrate count"
        #
        #         # get TimeScale
        #         videotimescale = int(streamindex.get('TimeScale', default=timescale))
        #
        #         # get the fragment url part
        #         urltemplate = streamindex.get('Url')
        #         assert urltemplate is not None, "empty urltemplate"
        #
        #         # get event times
        #         ds = list(map(lambda ee: int(ee.get('d')), streamindex.findall("c")))
        #         # add first fragment's timestamp
        #         ds.insert(int(streamindex.find('c').get('t', default='0')), 0)
        #         # duration of last fragment is not needed
        #         del ds[-1]
        #         assert len(ds) == int(streamindex.get('Chunks')), "fragment number mismatch: %d vs. %d" % (
        #             len(ds), int(streamindex.get('Chunks')))
        #
        #         for cd in np.cumsum(ds):
        #             self.schedulework(float(cd) / videotimescale,
        #                               self._videocurl,
        #                               server,
        #                               os.path.dirname(manifestpath) + "/" + urltemplate.replace(
        #                                   '{start time}', str(cd)).replace(
        #                                   '{bitrate}', str(strategy(bitrates)))
        #                               )
        #
        #     # get the StreamIndex for audio
        #     streamindex = root.find("StreamIndex[@Type='audio']")
        #     if streamindex is not None:
        #         # get the video bitrates
        #         bitrates = list(map(lambda element: int(element.get('Bitrate')), streamindex.findall('QualityLevel')))
        #         assert len(bitrates) != 0, "Empty bitrates"
        #
        #         # get TimeScale
        #         audiotimescale = int(streamindex.get('TimeScale', default=timescale))
        #
        #         # get the fragment url part
        #         urltemplate = streamindex.get('Url')
        #         assert urltemplate is not None, "empty urltemplate"
        #
        #         # get event times
        #         ds = list(map(lambda ee: int(ee.get('d')), streamindex.findall("c")))
        #         # add first fragment's timestamp
        #         ds.insert(int(streamindex.find('c').get('t', default='0')), 0)
        #         # duration of last fragment is not needed
        #         del ds[-1]
        #         assert len(ds) == int(streamindex.get('Chunks')), "fragment number mismatch: %d vs. %d" % (
        #             len(ds), int(streamindex.get('Chunks')))
        #
        #         for cd in np.cumsum(ds):
        #             self.schedulework(float(cd) / audiotimescale,
        #                               self._audiocurl,
        #                               server,
        #                               os.path.dirname(manifestpath) + "/" + urltemplate.replace(
        #                                   '{start time}', str(cd)).replace(
        #                                   '{bitrate}', str(strategy(bitrates)))
        #                               )
        #     manifestcurl.close()
        #
        # except pycurl.error as err:
        #     raise Exception("Cannot load %s, error message: %s" % ("http://%s%s" % (server, manifestpath), err))
        #
        # self._videocurl = pycurl.Curl()
        # self._audiocurl = pycurl.Curl()
        # self._videocurl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        # self._audiocurl.setopt(pycurl.WRITEFUNCTION, lambda x: None)

    def work(self, *args):
        if len(args) < 3 or len(args) > 5:
            raise SyntaxError("%s needs 3 arguments, got %d" % (self.__class__.__name__, len(args)))

        # TODO: implement checks
        curl = args[0]
        server = args[1]
        path = args[2]
        rfrom, rto = args[3] if len(args) == 4 else (None, None)

        url = "http://%s%s" % (server, path)

        curl.setopt(pycurl.URL, url)
        if rfrom is not None:
            curl.setopt(pycurl.RANGE, "%s-%s" % (rfrom, rto if rto is not None else ""))
        curl.perform()

        # check results
        statuscode = curl.getinfo(pycurl.HTTP_CODE)
        if statuscode in self._statuscodes:
            self._logdebug("'%s': %s" % (url, statuscode))
        else:
            self._logwarning("'%s': %s" % (url, statuscode))

    def cleanup(self):
        self._videocurl.close()
        self._audiocurl.close()
