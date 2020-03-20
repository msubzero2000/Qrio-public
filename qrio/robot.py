import arcade
import random

from config import Config
from utilities.vector import Vector
from utilities.affineTransform import AffineTransform
from animation import Animation
from robotPart import RobotPart
from animationCore import AnimationCore

from morphTargetCore import MorphTargetCore
from fidgetAnimationController import FidgetAnimationController
from morphTargetInterp import MorphTargetInterp
from brainStateMachine import BrainStateMachine


class Robot(object):
    _MAX_HAS_EYE_TARGET_STATE = 50  # Decide if we should be looking at a person/not based on the last 50 object detection states

    def __init__(self, screenSize):
        self._create(screenSize)

    def _create(self, screenSize):
        self._spriteList = arcade.SpriteList()

        self._robot = RobotPart(Vector(screenSize[0] / 2, screenSize[1] / 2), "images/dogbot/frame.png",
                                Config.SPRITE_SCALE, scale=Config.SPRITE_SCALE, name='body-frame')
        tail = RobotPart(Vector(255, -45), "images/dogbot/tail.png", Config.SPRITE_SCALE)
        self._robot.appendPart(tail)

        self._body = RobotPart(Vector(0, 0), "images/dogbot/body.png", Config.SPRITE_SCALE)
        self._robot.appendPart(self._body)

        headFrame = RobotPart(Vector(0, 0), "images/dogbot/frame.png", 1.0)

        self._body.appendPart(headFrame)
        leftEar, rightEar = self._createEars()

        headFrame.appendPart(leftEar)
        headFrame.appendPart(rightEar)

        head = RobotPart(Vector(-20, 0), "images/dogbot/head.png", Config.SPRITE_SCALE)
        headFrame.appendPart(head)

        leftEyeBase = self._createEye(Vector(-85, 320), "left-eye")
        head.appendPart(leftEyeBase)

        rightEyeBase = self._createEye(Vector(60, 320), "right-eye")
        head.appendPart(rightEyeBase)

        allSprites = self._robot.spriteList()

        for sprite in allSprites:
            self._spriteList.append(sprite)

        self._fidgetAnimation = FidgetAnimationController()

        self._createEyeTargetAnimation()

        self._brainState = BrainStateMachine()

    def _createEyeTargetAnimation(self):
        self._eyeTargetAnim = MorphTargetInterp()

        blackOffsetLeft = -19
        whiteOffsetLeft = blackOffsetLeft * 0.8
        blackOffsetRight = 15
        whiteOffsetRight = blackOffsetRight * 0.8

        blackOffsetTop = -15
        whiteOffsetTop = blackOffsetTop * 0.8
        blackOffsetBottom = 10
        whiteOffsetBottom = blackOffsetBottom * 0.8

        morphTarget = MorphTargetCore({'left-eye/white': Vector(whiteOffsetLeft, whiteOffsetTop),
                                       'left-eye/black': Vector(blackOffsetLeft, blackOffsetTop),
                                       'right-eye/white': Vector(whiteOffsetLeft, whiteOffsetTop),
                                       'right-eye/black': Vector(blackOffsetLeft, blackOffsetTop)
                                       })

        self._eyeTargetAnim.addMorpTarget(morphTarget, Vector(-0.5, -0.5))

        morphTarget = MorphTargetCore({'left-eye/white': Vector(whiteOffsetRight, whiteOffsetTop),
                                       'left-eye/black': Vector(blackOffsetRight, blackOffsetTop),
                                       'right-eye/white': Vector(whiteOffsetRight, whiteOffsetTop),
                                       'right-eye/black': Vector(blackOffsetRight, blackOffsetTop)
                                       })
        self._eyeTargetAnim.addMorpTarget(morphTarget, Vector(0.5, -0.5))

        morphTarget = MorphTargetCore({'left-eye/white': Vector(whiteOffsetRight, whiteOffsetBottom),
                                       'left-eye/black': Vector(blackOffsetRight, blackOffsetBottom),
                                       'right-eye/white': Vector(whiteOffsetRight, whiteOffsetBottom),
                                       'right-eye/black': Vector(blackOffsetRight, blackOffsetBottom)
                                       })
        self._eyeTargetAnim.addMorpTarget(morphTarget, Vector(0.5, 0.5))

        morphTarget = MorphTargetCore({'left-eye/white': Vector(whiteOffsetLeft, whiteOffsetBottom),
                                       'left-eye/black': Vector(blackOffsetLeft, blackOffsetBottom),
                                       'right-eye/white': Vector(whiteOffsetLeft, whiteOffsetBottom),
                                       'right-eye/black': Vector(blackOffsetLeft, blackOffsetBottom)
                                       })
        self._eyeTargetAnim.addMorpTarget(morphTarget, Vector(-0.5, 0.5))

        self._hasEyeTargetState = []

    def _createFace(self):
        return arcade.Sprite("images/dogbot/head.png", Config.SPRITE_SCALE)

    def _createEye(self, pos, namePrefix):
        eyeBase = RobotPart(pos, "images/dogbot/eye-white.png", Config.SPRITE_SCALE, name=namePrefix + "/white")
        eyeBlack = RobotPart(Vector(0, -10), "images/dogbot/eye-black.png", Config.SPRITE_SCALE, name=namePrefix + "/black")
        eyeBrow = RobotPart(Vector(-10, 70), "images/dogbot/eyebrow.png", Config.SPRITE_SCALE, name=namePrefix + "/eyebrow")

        eyeBase.appendPart(eyeBlack)
        eyeBase.appendPart(eyeBrow)

        return eyeBase

    def _createEars(self):
        leftEar = RobotPart(Vector(-180, 369), "images/dogbot/left-ear.png", Config.SPRITE_SCALE, name='left-ear')
        rightEar = RobotPart(Vector(192, 370), "images/dogbot/right-ear.png", Config.SPRITE_SCALE, name='right-ear')

        return leftEar, rightEar

    def addMorphTarget(self, morphTarget):
        # self._morphTargets.append(morphTarget)
        pass

    def spriteList(self):
        return self._spriteList

    def _updateAnimation(self):
        return self._fidgetAnimation.update()

    def _updateAnimationState(self, eyeTargetVecParam):
        self._hasEyeTargetState.append(eyeTargetVecParam is not None)
        # Keep the last n state
        if len(self._hasEyeTargetState) > self._MAX_HAS_EYE_TARGET_STATE:
            self._hasEyeTargetState = self._hasEyeTargetState[-self._MAX_HAS_EYE_TARGET_STATE:]

        # Work out the state
        totalHasEyeTarget = 0
        for curState in self._hasEyeTargetState:
            if curState:
                totalHasEyeTarget += 1

        newHaveEyeTarget = False
        if totalHasEyeTarget > len(self._hasEyeTargetState) / 2:
            newHaveEyeTarget = True

        self._brainState.update(newHaveEyeTarget)

    def update(self, lastFrameCaptured):
        self._brainState.update(lastFrameCaptured)

        eyeTargetVecParam, weight = self._brainState.getEyeTargetParam()
        # eyeTargetVecParam = None

        poseDict, rotDict = self._updateAnimation()
        if eyeTargetVecParam is not None:
            eyeTargetPoseDict = self._eyeTargetAnim.getPosAtVecParamForQuad(eyeTargetVecParam)
        else:
            eyeTargetPoseDict = {}

        for name, vec in poseDict.items():
            if name in eyeTargetPoseDict:
                if name in poseDict:
                    poseVec = poseDict[name].scale(1.0 - weight)
                    eyeTargetVec = eyeTargetPoseDict[name].scale(weight)
                    poseDict[name] = poseVec.add(eyeTargetVec)
                else:
                    poseDict[name] = eyeTargetPoseDict[name]

        t = AffineTransform()
        self._robot.update(t, poseDict, rotDict)
