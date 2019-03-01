from threading import Thread
import sched
import time
from io import BytesIO
import pycurl
from lxml import etree
import numpy as np
import os
from typing import Callable
import chardet
import random


class Ant(Thread):
    """
    A template, does not do anything.
    """

    def __init__(self, **kw):
        """
        An ant does work regurarly.

        Do not autostart here, otherwise it cannot be overloaded...
        :param kw: keyword arguments to forward to the Thread class
        """
        super(Ant, self).__init__(**kw)

        self._scheduler = sched.scheduler(time.time, time.sleep)

    def run(self):
        """
        Try not to overload this...
        :return:
        """
        print("%s '%s' born" % (self.__class__.__name__, self.name))

        # process tasks, this will block
        self._scheduler.run()

        # clean up stuff, if any
        self.cleanup()

        print("%s '%s' die" % (self.__class__.__name__, self.name))

    def schedulework(self, at, *args):
        """
        Schedule work for the ant.
        :param at: Time at work should be done
        :param args: Arguments passed to the work() method.
        :return:
        """
        self._scheduler.enter(delay=at, priority=100, action=self.work, argument=args)

    def work(self, *args):
        """
        Overload this, this is where the work is happening.
        :param args:
        :return:
        """
        pass

    def cleanup(self):
        """
        Called, when Ant dies to clean up stuff.
        :return:
        """
        pass


class HTTPAnt(Ant):
    """
    Accesses list of requests.
    """

    def __init__(self, server: str, paths, delays, host: str = None, **kw):
        super(HTTPAnt, self).__init__(**kw)
        assert len(paths) == len(delays), "length mismatch: %d vs. %d" % (len(paths), len(delays))

        self._server = server

        for path, delay in zip(paths, delays):
            self.schedulework(delay, path)

        self._curl = pycurl.Curl()
        self._curl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        if host is not None:
            self._curl.setopt(pycurl.HTTPHEADER, ['Host: %s' % host])

    def work(self, *args):
        path = args[0]

        self._curl.setopt(pycurl.URL, "http://%s%s" % (self._server, path))
        self._curl.perform()

        # if int(self._curl.getinfo(pycurl.HTTP_CODE)) != 200:
        #    raise Exception("cannot load %s, return code: %d" % ("http://%s%s" % (self._server, path), self._curl.getinfo(pycurl.HTTP_CODE)))

    def cleanup(self):
        self._curl.close()


class ABRAnt(Ant):
    """
    Smooth streaming
    """

    def __init__(self, server: str, manifestpath, strategy, host: str = None, **kw):
        assert isinstance(strategy, Callable), "Strategy must be callable: '%s'" % strategy
        super(ABRAnt, self).__init__(**kw)

        self._videocurl = pycurl.Curl()
        self._audiocurl = pycurl.Curl()
        self._videocurl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        self._audiocurl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        # fragmentsched = sched.scheduler(time.time, time.sleep)

        manifestcurl = pycurl.Curl()

        if host is not None:
            manifestcurl.setopt(pycurl.HTTPHEADER, ['Host: %s' % host])
            self._videocurl.setopt(pycurl.HTTPHEADER, ['Host: %s' % host])
            self._audiocurl.setopt(pycurl.HTTPHEADER, ['Host: %s' % host])

        try:
            manifestcurl.setopt(pycurl.URL, "http://%s%s" % (server, manifestpath))
            response = BytesIO()
            manifestcurl.setopt(pycurl.WRITEDATA, response)
            manifestcurl.perform()

            if int(manifestcurl.getinfo(pycurl.HTTP_CODE)) != 200:
                raise Exception(
                    "cannot load %s, return code: %d" % (manifestcurl.geturl(), manifestcurl.getinfo(pycurl.HTTP_CODE)))

            manifestcurl.close()

            # parse XML and fuck Microsoft!
            charset = chardet.detect(response.getvalue())['encoding']
            manifest = response.getvalue().decode(charset).encode(charset)
            root = etree.fromstring(manifest)

            # validate manifest
            assert root.tag == 'SmoothStreamingMedia', "Invalid root tag: '%s'" % root.tag
            assert root.get('MajorVersion') == '2', "Invalid Major version: '%s'" % root.get('MajorVersion')

            # get TimeScale
            timescale = root.get('TimeScale', default='10000000')

            # get the StreamIndex for video
            streamindex = root.find("StreamIndex[@Type='video']")
            if streamindex is not None:
                # get the video bitrates
                bitrates = list(map(lambda element: int(element.get('Bitrate')), streamindex.findall('QualityLevel')))
                assert len(bitrates) == int(streamindex.get('QualityLevels')), "invalid bitrate count"

                # get TimeScale
                videotimescale = int(streamindex.get('TimeScale', default=timescale))

                # get the fragment url part
                urltemplate = streamindex.get('Url')
                assert urltemplate is not None, "empty urltemplate"

                # get event times
                ds = list(map(lambda ee: int(ee.get('d')), streamindex.findall("c")))
                # add first fragment's timestamp
                ds.insert(int(streamindex.find('c').get('t', default='0')), 0)
                # duration of last fragment is not needed
                del ds[-1]
                assert len(ds) == int(streamindex.get('Chunks')), "fragment number mismatch: %d vs. %d" % (
                    len(ds), int(streamindex.get('Chunks')))

                for cd in np.cumsum(ds):
                    self.schedulework(float(cd) / videotimescale,
                                      self._videocurl,
                                      server,
                                      os.path.dirname(manifestpath) + "/" + urltemplate.replace(
                                          '{start time}', str(cd)).replace(
                                          '{bitrate}', str(strategy(bitrates)))
                                      )

            # get the StreamIndex for audio
            streamindex = root.find("StreamIndex[@Type='audio']")
            if streamindex is not None:
                # get the video bitrates
                bitrates = list(map(lambda element: int(element.get('Bitrate')), streamindex.findall('QualityLevel')))
                assert len(bitrates) != 0, "Empty bitrates"

                # get TimeScale
                audiotimescale = int(streamindex.get('TimeScale', default=timescale))

                # get the fragment url part
                urltemplate = streamindex.get('Url')
                assert urltemplate is not None, "empty urltemplate"

                # get event times
                ds = list(map(lambda ee: int(ee.get('d')), streamindex.findall("c")))
                # add first fragment's timestamp
                ds.insert(int(streamindex.find('c').get('t', default='0')), 0)
                # duration of last fragment is not needed
                del ds[-1]
                assert len(ds) == int(streamindex.get('Chunks')), "fragment number mismatch: %d vs. %d" % (
                    len(ds), int(streamindex.get('Chunks')))

                for cd in np.cumsum(ds):
                    self.schedulework(float(cd) / audiotimescale,
                                      self._audiocurl,
                                      server,
                                      os.path.dirname(manifestpath) + "/" + urltemplate.replace(
                                          '{start time}', str(cd)).replace(
                                          '{bitrate}', str(strategy(bitrates)))
                                      )

        except pycurl.error as err:
            print("cannot load %s, error message: %s" % ("http://%s%s" % (server, manifestpath), err))
        except Exception as e:
            print(e)

        manifestcurl.close()

    def work(self, *args):
        curl = args[0]
        server = args[1]
        path = args[2]

        curl.setopt(pycurl.URL, "http://%s%s" % (server, path))
        curl.perform()

    def cleanup(self):
        self._videocurl.close()
        self._audiocurl.close()
