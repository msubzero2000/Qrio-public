import os

from utilities.vector import Vector


class EyeCoordMapper(object):

    def __init__(self):
        pass

    def transform(self, objCoord):
        # To calculate the puppet eye coordinate (-0.5 -> 0.5) in order to look at the object at objCoord
        eyeCoord = objCoord.subtract(Vector(0.5, 0.5))

        return eyeCoord
