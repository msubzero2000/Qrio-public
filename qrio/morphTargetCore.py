import os


class MorphTargetCore(object):

    def __init__(self, poseDict, rotDict=None):
        self._poseDict = poseDict
        self._rotDict = rotDict

    def getWithWeight(self, weight=1.0, name=None):
        outPoseDict = {}
        outRotDict = {}

        for key, vec in self._poseDict.items():
            if name is None or name in outPoseDict:
                outPoseDict[key] = vec.scale(weight)

        if self._rotDict is not None:
            for key, val in self._rotDict.items():
                if name is None or name in outRotDict:
                    outRotDict[key] = val * weight

        return outPoseDict, outRotDict
