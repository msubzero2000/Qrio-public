import os

from morphTargetCore import MorphTargetCore


class KeyFrameAnimation(object):

    def __init__(self, morphTargetStart:MorphTargetCore, morphTargetEnd:MorphTargetCore):
        self._morphTargetStart = morphTargetStart
        self._morphTargetEnd = morphTargetEnd

    def getPosAt(self, t, name=None):
        outPoseDictStart, outRotDictStart = self._morphTargetStart.getWithWeight(1.0 - t, name)
        outPoseDictStop, outRotDictStop = self._morphTargetEnd.getWithWeight(t, name)

        finalOutPoseDict = {}
        finalOutRotDict = {}

        for key, vec in outPoseDictStart.items():
            if key in outPoseDictStop:
                finalOutPoseDict[key] = outPoseDictStart[key].add(outPoseDictStop[key])

        for key, vec in outRotDictStart.items():
            if key in outRotDictStop:
                finalOutRotDict[key] = outRotDictStart[key] + outRotDictStop[key]

        return finalOutPoseDict, finalOutRotDict

    def getMorphTargetEnd(self):
        return self._morphTargetEnd

    def getMorphTargetStart(self):
        return self._morphTargetStart


class AnimationCore(object):

    def __init__(self, morphTargetStart:MorphTargetCore, morphTargetEnd:MorphTargetCore, speed=0.01, pauseAtStart=0):
        self._keyFrameAnimation = KeyFrameAnimation(morphTargetStart, morphTargetEnd)
        self._speed = speed
        self._curT = 0
        self._done = False
        self._pauseAtStart = pauseAtStart

    def update(self):
        if self._done:
            return None, None

        if self._curT >= 1:
            # Terminate animation in the next iteration
            self._done = True

        poseDict, rotDict = self._keyFrameAnimation.getPosAt(min(1, self._curT))

        # Don't increment timer if we are still at pause period
        if self._pauseAtStart > 0:
            self._pauseAtStart -= 1
        else:
            self._curT += self._speed

        return poseDict, rotDict

    def getMorphTargetEnd(self):
        return self._keyFrameAnimation.getMorphTargetEnd()

    def getMorphTargetStart(self):
        return self._keyFrameAnimation.getMorphTargetStart()
