from ants import Egg, Ant, Queen


class Simplequeen(Queen):
    def layeggs(self):
        for i in range(0, 6):
            yield Egg(i, larv=Ant, name=str(i))
