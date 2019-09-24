from unittest import TestCase
from ants import ABRAnt


class TestABRAnt(TestCase):
    def test_abrant(self):
        testant = ABRAnt(server="playready.directtaps.net",
                     manifestpath="/smoothstreaming/TTLSS720VC1/To_The_Limit_720.ism/Manifest",
                     strategy=min,
                     duration=30)

        testant.start()
