from threading import Thread
import sched, time
from io import BytesIO
import pycurl
from urllib.parse import urlparse
from lxml import etree
import numpy as np
import os
from typing import Callable
import random


class Ant(Thread):
    """
    A template, does not do anything.
    """

    def __init__(self, **kw):
        super().__init__(**kw)

        self._scheduler = sched.scheduler(time.time, time.sleep)

    def run(self):
        print("%s '%s' born" % (self.__class__.__name__, self.name))

        # process tasks, this will block
        self._scheduler.run()

        print("%s '%s' die" % (self.__class__.__name__, self.name))

    def schedulework(self, at, *args):
        self._scheduler.enter(delay=at, priority=100, action=self.work, argument=args)

    def work(self, *args, **kwargs):
        pass


class HTTPAnt(Ant):
    """
    Accesses list of requests.
    """

    def __init__(self, server, paths, delays, **kw):
        super().__init__(**kw)
        assert len(paths) == len(delays), "length mismatch: %d / %d" % (len(paths), len(delays))

        self._server = server

        for path, delay in zip(paths, delays):
            self.schedulework(delay, path)
        #            print(path, delay)

        self._curl = pycurl.Curl()
        self._curl.setopt(pycurl.WRITEFUNCTION, lambda x: None)

    def work(self, *args):
        path = args[0]

        self._curl.setopt(pycurl.URL, "http://%s%s" % (self._server, path))
        self._curl.perform()

        # if int(self._curl.getinfo(pycurl.HTTP_CODE)) != 200:
        #    raise Exception("cannot load %s, return code: %d" % ("http://%s%s" % (self._server, path), self._curl.getinfo(pycurl.HTTP_CODE)))

    def run(self):
        super().run()
        self._curl.close()


class ABRAnt(Ant):
    """
    Smooth streaming
    """

    def __init__(self, manifest, strategy, **kw):
        assert isinstance(strategy, Callable), "Strategy must be callable: '%s'" % strategy

        super().__init__(**kw)

        self.schedulework(0, manifest)
        self._strategy = strategy

    def work(self, *args):
        manifest = urlparse(args[0])

        videoant = None
        audioant = None

        mycurl = pycurl.Curl()
        try:
            mycurl.setopt(pycurl.URL, manifest.geturl())
            response = BytesIO()
            mycurl.setopt(pycurl.WRITEDATA, response)
            mycurl.perform()

            if int(mycurl.getinfo(pycurl.HTTP_CODE)) != 200:
                raise Exception("cannot load %s, return code: %d" % (mycurl.get, mycurl.getinfo(pycurl.HTTP_CODE)))

            f = response.getvalue().decode('iso-8859-1').encode('ascii')

            # parse XML
            root = etree.fromstring(f)

            # validate manifest
            assert root.tag == 'SmoothStreamingMedia', "Invalid root tag: '%s'" % root.tag
            assert root.get('MajorVersion') == '2', "Invalid Major version: '%s'" % root.get('MajorVersion')

            # get the StreamIndex for video
            streamindex = root.find("StreamIndex[@Type='video']")
            if streamindex is not None:
                # get the video bitrates
                bitrates = list(map(lambda e: int(e.get('Bitrate')), streamindex.findall('QualityLevel')))
                assert len(bitrates) != 0, "Empty bitrates"

                # get TimeScale
                timescale = streamindex.get('TimeScale')
                assert timescale is not None
                timescale = int(timescale)

                # get the fragment url part
                urltemplate = streamindex.get('Url')
                assert urltemplate is not None, "empty urltemplate"

                c = streamindex.find("c[@t]")
                ds = list(map(lambda e: int(e.get('d')), streamindex.findall("c")))
                assert np.std(ds) < np.average(ds) * 0.5, "deviation of d values are greater than 5%%: %f/%f" % (
                    np.std(ds), np.average(ds))

                ds.insert(int(c.get("t")), 0)
                cds = np.cumsum(ds)
                assert len(cds) == int(streamindex.get('Chunks')) + 1, len(cds)

                videoant = HTTPAnt(name="%s-vid" % self.name, server=manifest.netloc,
                                   paths=list(map(
                                       lambda t: os.path.dirname(manifest.path) +
                                                 "/" +
                                                 urltemplate.replace('{start time}', str(t))
                                                     .replace('{bitrate}', str(self._strategy(bitrates))),
                                       cds)),
                                   delays=list(map(lambda d: d / timescale, cds))
                                   )

            # get the StreamIndex for audio
            streamindex = root.find("StreamIndex[@Type='audio']")
            if streamindex is not None:
                # get the video bitrates
                bitrates = list(map(lambda e: int(e.get('Bitrate')), streamindex.findall('QualityLevel')))
                assert len(bitrates) != 0, "Empty bitrates"

                # get TimeScale
                timescale = streamindex.get('TimeScale')
                assert timescale is not None
                timescale = int(timescale)

                # get the fragment url part
                urltemplate = streamindex.get('Url')
                assert urltemplate is not None, "empty urltemplate"

                c = streamindex.find("c[@t]")
                ds = list(map(lambda e: int(e.get('d')), streamindex.findall("c")))
                assert np.std(ds) < np.average(ds) * 0.5, "deviation of d values are greater than 5%%: %f/%f" % (
                    np.std(ds), np.average(ds))

                ds.insert(int(c.get("t")), 0)
                cds = np.cumsum(ds)
                assert len(cds) == int(streamindex.get('Chunks')) + 1, len(cds)

                audioant = HTTPAnt(name="%s-aud" % self.name, server=manifest.netloc,
                                   paths=list(map(
                                       lambda t: os.path.dirname(manifest.path) +
                                                 "/" +
                                                 urltemplate.replace('{start time}', str(t))
                                                     .replace('{bitrate}', str(self._strategy(bitrates))),
                                       cds)),
                                   delays=list(map(lambda d: d / timescale, cds))
                                   )

        except pycurl.error as err:
            print("cannot load %s, error message: %s" % (manifest.geturl(), err))
        finally:
            mycurl.close()

        print("Downloading manifest %s" % manifest.geturl())

        videoant.start()
        audioant.start()

        videoant.join()
        audioant.join()

        # done
