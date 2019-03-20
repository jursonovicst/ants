from ants import Egg, SleepyAnt, Queen


class Simplequeen(Queen):
    def layeggs(self):
        for i in range(0, 6):
            yield Egg(i, larv=SleepyAnt, name=str(i), sleepperiod=5)
