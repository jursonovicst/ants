from ants import Egg, ABRAnt, Queen


# start one HSS stream 5 seconds after simulation start. Use the maximal bitrate profile.
class Simplequeen(Queen):

    def layeggs(self):

        # lay one egg
        yield Egg(5,                       # egg hatches 5 seconds after simulation start
                  larv=ABRAnt,             # an ABRAnt will hatch from this egg
                  name="TTL 720p VC1 CLEAR", # name of the Ant
                  server="playready.directtaps.net", # streaming server
                  manifestpath="/smoothstreaming/TTLSS720VC1/To_The_Limit_720.ism/Manifest",  # path of the manifest
                  strategy=max)            # bitrate switching strategy, this function will return one value of the
                                           # bitrates, which will be handed over as a list in the first argument.
