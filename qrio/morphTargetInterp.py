import os

from morphTargetCore import MorphTargetCore
from utilities.vector import Vector


class MorphTargetInterp(object):

    def __init__(self):
        self._morphTargets = []

    def addMorpTarget(self, morphTarget, vecParamAtTarget):
        self._morphTargets.append((morphTarget, vecParamAtTarget))

    def getPosAtVecParamForQuad(self, vecParam):
        finalPos = {}

        lowerLeftPos, _ = self._morphTargets[0][0].getWithWeight(1.0)
        lowerRightPos, _ = self._morphTargets[1][0].getWithWeight(1.0)
        upperLeftPos, _ = self._morphTargets[3][0].getWithWeight(1.0)

        weightX = (vecParam.x - self._morphTargets[0][1].x) / (self._morphTargets[1][1].x - self._morphTargets[0][1].x)
        weightY = (vecParam.y - self._morphTargets[1][1].y) / (self._morphTargets[2][1].y - self._morphTargets[1][1].y)

        for name, vec in lowerLeftPos.items():
            finalVec = Vector(lowerLeftPos[name].x * (1.0 - weightX) + lowerRightPos[name].x * weightX,
                              lowerLeftPos[name].y * (1.0 - weightY) + upperLeftPos[name].y * weightY)

            finalPos[name] = finalVec

        return finalPos

    def getPosAtVecParam(self, vecParam):
        totalWeight = 0
        finalPos = {}

        for morphTarget, vecParamAtTarget in self._morphTargets:
            curDist = max(0.01, vecParam.subtract(vecParamAtTarget).length())
            weight = 1.0 / curDist
            totalWeight += weight
            curPos = morphTarget.getWithWeight(weight)

            for name, vec in curPos.items():
                if name in finalPos:
                    finalPos[name] = finalPos[name].add(vec)
                else:
                    finalPos[name] = vec

        normPos = {}
        for name, vec in finalPos.items():
            normPos[name] = vec.scale(1.0 / totalWeight)

        return normPos
