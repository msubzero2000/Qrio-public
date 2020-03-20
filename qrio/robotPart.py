import arcade

from utilities.affineTransform import AffineTransform
from utilities.vector import Vector
from morphTarget import MorphTarget


class RobotPart(object):

    def __init__(self, relativeNaturalPos, imagePath, spriteScale=1.0, name=None, scale=1.0,
                 rotation=0.0):
        self._name = name

        if self._name is None:
            self._name = imagePath.split("/")[-1].split(".")[0]

        self._relativeNaturalPos = relativeNaturalPos
        self._scale = scale
        self._rotation = rotation
        self._sprite = arcade.Sprite(imagePath, spriteScale)
        self._parts = []

    def spriteList(self):
        spriteList = [self._sprite]

        for part in self._parts:
            spriteList.extend(part.spriteList())

        return spriteList

    def _getFinalMorphTargetPos(self, paramVec:Vector, morphTargets:[MorphTarget]):
        # paramVec = Vector(0.5, -0.5)

        finalPos = Vector(0, 0)
        totalWeight = 0.0

        for target in morphTargets:
            curPos, weight = target.getAt(self._name, paramVec)
            # curPos = Vector(30.0, 30.0)
            # weight = 1.0

            # curPos = target.getAt(self._name, paramVec)
            totalWeight += weight
            if curPos is not None:
                finalPos = finalPos.add(curPos)

        return finalPos.scale(totalWeight)

    def _getPoseAt(self, poseDict):
        if self._name in poseDict:
            return poseDict[self._name]

        return None

    def _getRotAt(self, rotDict):
        if self._name in rotDict:
            return rotDict[self._name]

        return None

    def update(self, trans: AffineTransform, poseDict, rotDict):
        # Further transform (carried from parent transform) by current natural pose offset
        trans.translate(self._relativeNaturalPos)
        animOffset = self._getPoseAt(poseDict)

        # Apply animation offset
        if animOffset is not None:
            trans.translate(animOffset)

        # Apply scale transform
        trans.scale(self._scale)

        animRot = self._getRotAt(rotDict)

        # Extract the translation of current transform
        pos = trans.getTranslation()
        self._sprite.center_x = pos.x
        self._sprite.center_y = pos.y

        # Apply rotation base transform
        trans.rotate(self._rotation)

        # Apply animation transform
        if animRot is not None:
            trans.rotate(animRot)

        # Extract the current rotation angle
        rotAngle = trans.getRotation()

        self._sprite.angle = rotAngle

        for part in self._parts:
            # Propagate the current transform the all children
            subTrans = trans.copy()
            part.update(subTrans, poseDict, rotDict)

    def appendPart(self, part):
        self._parts.append(part)
