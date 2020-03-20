import os

from utilities.vector import Vector


class MorphTarget(object):

    def __init__(self, paramVecAtTarget, posDict):
        self._paramVecAtTarget = paramVecAtTarget
        self._posDict = posDict

    def getAt(self, name, curParamVec):
        if name in self._posDict:
            deltaVec = curParamVec.subtract(self._paramVecAtTarget)
            dist = max(1, deltaVec.length())
            weight = 1.0 / dist

            return self._posDict[name].scale(weight), weight

        return None, 0.0
