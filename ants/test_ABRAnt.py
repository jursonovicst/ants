from unittest import TestCase
from ants import ABRAnt


class TestABRAnt(TestCase):
    def test_abrant(self):
        ant = ABRAnt(server="playready.directtaps.net",
                     manifestpath="/smoothstreaming/TTLSS720VC1/To_The_Limit_720.ism/Manifest",
                     strategy=min,
                     length = 30)

        ant.start()
        ant.join()
#        ant = ABRAnt(server="dash01.dmm.t-online.de",
#                     manifestpath="/dash04/dashstream/streaming/mgm_serien/9221438342941160219/636480717292137630/Jezebels_Reich-Main_Movie-9221571562371948872_v1_deu_20_1080k-HEVC-SD_HD_HEVC_DASH.mpd?streamProfile=Dash-NoText",
#                     strategy= min)
#        print(ant)
