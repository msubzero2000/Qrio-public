import os
import random

from morphTargetCore import MorphTargetCore
from utilities.vector import Vector
from animationCore import AnimationCore
from config import Config


class FidgetAnimationController(object):

    _FPS = int(max(1, Config.PLAYBACK_FPS))

    def __init__(self):
        self._animationList = []

        self._eyeAnimationCtr = 0
        self._leftEarAnimationCtr = 0
        self._rightEarAnimationCtr = 0
        self._headAnimationCtr = 0
        self._tailAnimationCtr = 0

        self._animationList.append((None, self._createEyeFidgetAnimation))
        self._animationList.append((None, self._createLeftEarFidgetAnimation))
        self._animationList.append((None, self._createRightEarFidgetAnimation))
        self._animationList.append((None, self._createHeadFidgetAnimation))
        self._animationList.append((None, self._createTailFidgetAnimation))

        for idx, (anim, createFunc) in enumerate(self._animationList):
            anim = createFunc()
            self._animationList[idx] = (anim, createFunc)

    def _createEyeFidgetAnimation(self, prevAnim=None):
        if prevAnim is not None:
            morphTargetAtStart = prevAnim.getMorphTargetEnd()
        else:
            morphTargetAtStart = MorphTargetCore({
                                                  'left-eye/white': Vector(0, 0),
                                                  'left-eye/black': Vector(0, 0),
                                                  'right-eye/white': Vector(0, 0),
                                                  'right-eye/black': Vector(0, 0)
                                                  })

        eyeTargetOffsetX = random.randrange(-15, 15)
        eyeTargetOffsetY = random.randrange(-15, 5)

        morphTargetAtStop = MorphTargetCore({
                                             'left-eye/black': Vector(eyeTargetOffsetX, eyeTargetOffsetY),
                                             'left-eye/white': Vector(int(eyeTargetOffsetX * 0.8), int(eyeTargetOffsetY * 0.8)),
                                             'right-eye/black': Vector(eyeTargetOffsetX, eyeTargetOffsetY),
                                             'right-eye/white': Vector(int(eyeTargetOffsetX * 0.8),
                                                                      int(eyeTargetOffsetY * 0.8))
                                             })
        # Pause every x second
        pauseAtStart = random.randrange(self._FPS * 2, self._FPS * 4)
        self._eyeAnimationCtr += 1

        return AnimationCore(morphTargetAtStart, morphTargetAtStop, Config.speedScale(0.03), pauseAtStart)

    def _createHeadFidgetAnimation(self, prevAnim=None):
        if prevAnim is not None:
            morphTargetAtStart = prevAnim.getMorphTargetEnd()
        else:
            morphTargetAtStart = MorphTargetCore({'frame': Vector(0, 0)},
                                                 {'frame': 0})

        headTargetOffsetY = random.randrange(-5, 4)
        headRotationOffset = random.randrange(-10, 10)
        morphTargetAtStop = MorphTargetCore({'frame': Vector(0, int(headTargetOffsetY))
                                            },
                                            {'frame': headRotationOffset
                                            })
        # Pause every x second
        pauseAtStart = random.randrange(self._FPS * 1, self._FPS * 3)
        self._headAnimationCtr += 1

        return AnimationCore(morphTargetAtStart, morphTargetAtStop, Config.speedScale(0.02), pauseAtStart)

    def _createTailFidgetAnimation(self, prevAnim=None):
        if prevAnim is not None:
            morphTargetAtStart = prevAnim.getMorphTargetEnd()
            morphTargetAtStop = prevAnim.getMorphTargetStart()
        else:
            morphTargetAtStart = MorphTargetCore({'tail': Vector(0, 0)},
                                                 {'tail': 0})
            tailRotationOffset = random.randrange(-30, -20)
            morphTargetAtStop = MorphTargetCore({'tail': Vector(0, 0)
                                                },
                                                {'tail': tailRotationOffset
                                                })

        pauseAtStart = 0
        if self._tailAnimationCtr % 6 == 0:
            # Pause every x second
            pauseAtStart = random.randrange(self._FPS * 3, self._FPS * 8)

        self._tailAnimationCtr += 1

        return AnimationCore(morphTargetAtStart, morphTargetAtStop, Config.speedScale(0.3), pauseAtStart)

    def _createLeftEarFidgetAnimation(self, prevAnim=None):
        # Alternate moving from start to stop
        if prevAnim is not None:
            morphTargetAtStart = prevAnim.getMorphTargetEnd()
            morphTargetAtStop = prevAnim.getMorphTargetStart()
        else:
            morphTargetAtStart = MorphTargetCore({'left-ear': Vector(0, 0)},
                                                 {'left-ear': 0})
            earTargetOffsetX = random.randrange(-2, 2)
            earTargetOffsetY = random.randrange(20, 30)
            morphTargetAtStop = MorphTargetCore({'left-ear': Vector(earTargetOffsetX, earTargetOffsetY)},
                                                {'left-ear': -10})

        pauseAtStart = 0
        if self._leftEarAnimationCtr % 4 == 0:
            # Pause every x second
            pauseAtStart = random.randrange(self._FPS * 3, self._FPS * 8)

        self._leftEarAnimationCtr += 1

        return AnimationCore(morphTargetAtStart, morphTargetAtStop, Config.speedScale(0.2), pauseAtStart)

    def _createRightEarFidgetAnimation(self, prevAnim=None):
        # Alternate moving from start to stop
        if prevAnim is not None:
            morphTargetAtStart = prevAnim.getMorphTargetEnd()
            morphTargetAtStop = prevAnim.getMorphTargetStart()
        else:
            morphTargetAtStart = MorphTargetCore({'right-ear': Vector(0, 0)},
                                                 {'right-ear': 0})
            earTargetOffsetX = random.randrange(-2, 2)
            earTargetOffsetY = random.randrange(20, 30)
            morphTargetAtStop = MorphTargetCore({'right-ear': Vector(earTargetOffsetX, earTargetOffsetY)},
                                                {'right-ear': 10})

        pauseAtStart = 0
        if self._rightEarAnimationCtr % 4 == 0:
            # Pause every x second
            pauseAtStart = random.randrange(self._FPS * 3, self._FPS * 8)

        self._rightEarAnimationCtr += 1

        return AnimationCore(morphTargetAtStart, morphTargetAtStop, Config.speedScale(0.2), pauseAtStart)

    def update(self):
        finalPoseDict = {}
        finalRotDict = {}

        for idx, (anim, createFunc) in enumerate(self._animationList):
            poseDict, rotDict = anim.update()

            if poseDict is None:
                anim = createFunc(anim)
                self._animationList[idx] = (anim, createFunc)
                poseDict, rotDict = anim.update()

            for name, vec in poseDict.items():
                if name in finalPoseDict:
                    finalPoseDict[name].add(vec)
                else:
                    finalPoseDict[name] = vec

            for name, vec in rotDict.items():
                if name in finalRotDict:
                    finalRotDict[name].add(vec)
                else:
                    finalRotDict[name] = vec

        return finalPoseDict, finalRotDict
