import os


class Animation(object):

    def __init__(self, targetVec, speed=0.01):
        self._targetVec = targetVec
        self._paramT = 0.0
        self._speed = speed
        self._animating = True

    def update(self):
        self._paramT += self._speed
        if self._paramT > 1.0:
            self._paramT = 1.0
            self._animating = False

            # Done animating
            return True

        # Still animating
        return False

    def paramT(self):
        return self._paramT
