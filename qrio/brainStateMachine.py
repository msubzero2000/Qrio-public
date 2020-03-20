import os

from intent import Intent
from eyeCoordMapper import EyeCoordMapper
from objectDetection import ObjectName
from utilities.stopwatch import Stopwatch
from config import Config


class BrainState(object):
    Idle = "Idle"
    Engaging = "Engaging"
    Conversing = "Conversing"
    ObjectRecognised = "ObjectRecognised"
    PlayingVideo = "PlayingVideo"
    FinishPlayingVideo = "FinishPlayingVideo"
    FailedPlayingVideo = "FailedPlayingVideo"
    AskToBringAnotherObject = "AskToBringAnotherObject"


class TargetName(object):
    Other = "Other"
    Yumi = "Yumi"
    Gus = "Gus"
    Dexie = "Dexie"


class TargetDistance(object):
    Close = "Close"
    Far = "Far"


class BrainStateMachine(object):
    _MAX_ENGAGED_TARGET_HISTORY = 5
    # We don't want to scale the focus_eye_speed excesively so keep it at 0.2
    _FOCUS_EYE_SPEED = 0.2
    _DISSENGAGED_PATIENCE = Config.frameScale(1000) # If no target for 1000 iterations then totally disengaged
    _EYE_MOVEMENT_SMOOTHING_FACTOR = 0.2    # The higher the slower the eye will move to new position
    _TIME_TO_FULLY_ENGAGED = Config.frameScale(300)    # Start asking to bring object after the start of engagement state
    _DELAY_BEFORE_ASKING_REPEAT_QUESTION = Config.frameScale(30)   # Ask to bring an object after x second not seeing any
    _LOCK_OBJECT_PATIENCE = Config.frameScale(180) # If person is no longer visible for 100 iterations, unlock object
    _TIMES_SEEN_TO_CONSIDER_OBJECT_REAL = 3 # An object has to be seen 20/60 frames to be considered as a real object
    _NO_EYE_TARGET_PATIENCE = Config.frameScale(120) # If no target to see in x frames start doing eye fidget

    def __init__(self):
        self._state = BrainState.Idle
        self._currentStateTime = None
        self._engagedTargets = []
        self._currentTarget = None
        self._engagementWeight = 0.0
        self._timeToDissengaged = 0
        self._sameObjectWasDetected = False
        self._timeEngaged = 0
        self._currentTargetFocusWeight = 0.0
        self._currentEyeCenter = None
        self._currentTargetFocusWeight = 0
        self._currentTargetDistance = None
        self._currentTargetName = None
        self._objectTarget = None
        self._targetDistance = 0
        self._lockedObjectTarget = None
        self._eyeCoordMapper = EyeCoordMapper()
        self._isSetupReady = False
        self._intent = None
        self._startCtr = 0
        self._timeToReleaseLockedObject = 0
        self._seenObject = None
        self._prevSeenObject = None
        self._seenSameObjectCtr = 0
        self._noEyeTargetTimer = 0

    def _updateObjectTarget(self, lastFrameCaptured):
        objectTarget, targetDistance = lastFrameCaptured.findNewObject(objectName=None, exclusionNames={ObjectName.Person})

        canRecordObject = True
        self._sameObjectWasDetected = False

        self._prevSeenObject = self._seenObject
        self._seenObject = objectTarget

        realObjectTarget = None
        # Only consider an object seen a few times in a row to avoid blip
        if self._seenObject is not None and self._prevSeenObject is not None:
            if self._seenObject.name == self._prevSeenObject.name:
                self._seenSameObjectCtr += 1
                if self._seenSameObjectCtr >= self._TIMES_SEEN_TO_CONSIDER_OBJECT_REAL:
                    realObjectTarget = self._seenObject
            else:
                self._seenSameObjectCtr = 0
        else:
            self._seenSameObjectCtr = 0

        # Make sure we don't re-recognise the same object after playing the video about this object
        if realObjectTarget is not None:
            if self._lockedObjectTarget is not None:
                if objectTarget.name == self._lockedObjectTarget.name:
                    canRecordObject = False
                    self._sameObjectWasDetected = True

        if canRecordObject:
            self._objectTarget = realObjectTarget
            self._targetDistance = targetDistance
        else:
            self._objectTarget = None
            self._targetDistance = 0

        if self._objectTarget is not None:
            print("Detecting {0}".format(self._objectTarget.name))

    def _updateEyeTarget(self, lastFrameCaptured):
        newEngagedTarget, newTargetDistance = self._getPersonToEngage(lastFrameCaptured)

        self._engagedTargets.append((newEngagedTarget, newTargetDistance))

        if len(self._engagedTargets) >= self._MAX_ENGAGED_TARGET_HISTORY:
            self._engagedTargets = self._engagedTargets[-self._MAX_ENGAGED_TARGET_HISTORY:]

        totalHasTarget = 0
        targetMinDistance = None

        # Look back through all history to decide if we currently have a target
        # This is done to avoid state flickering
        for target, targetDistance in self._engagedTargets:
            if target is not None:
                totalHasTarget += 1

                if targetMinDistance is None or targetDistance < targetMinDistance:
                    targetMinDistance = targetDistance

        if totalHasTarget > self._MAX_ENGAGED_TARGET_HISTORY / 2:
            # We have a target. Pick the target which is always the last in the stack
            for i in range(len(self._engagedTargets) - 1, 0, -1):
                if self._engagedTargets[i] is not None:
                    self._lockToTarget(self._engagedTargets[-1])
                    break
        else:
            self._releaseTarget()

    def _updateBrainState(self):
        if self._intent.isBusy():
            return

        # Don't change our state if we are currently talking
        newState = self._state

        # If have target, set state to engaging
        if self._currentTarget is not None:
            # If we were engaging and already asked the person to come then we jump into conversing
            if self._state == BrainState.Engaging:
                self._timeEngaged += 1

                if self._timeEngaged >= self._TIME_TO_FULLY_ENGAGED:
                    newState = BrainState.Conversing
                    self._intent.askToBringObject()
            elif self._state == BrainState.Idle:
                self._timeEngaged = 0
                newState = BrainState.Engaging
                self._intent.askToComeAndPlay()
            elif self._state == BrainState.Conversing:
                if self._objectTarget is not None:
                    newState = BrainState.ObjectRecognised
                    self._lockedObjectTarget = self._objectTarget
                    self._timeToReleaseLockedObject = self._LOCK_OBJECT_PATIENCE
                    self._intent.objectRecognised(self._lockedObjectTarget.name)
                else:
                    if self._currentStateTime is not None and self._currentStateTime.get() / 1000 >= self._DELAY_BEFORE_ASKING_REPEAT_QUESTION:
                        if self._sameObjectWasDetected and self._lockedObjectTarget is not None:
                            self._intent.askToBringNewObject(self._lockedObjectTarget.name)
                        else:
                            self._intent.askToBringObject()

                        newState = BrainState.AskToBringAnotherObject
            elif self._state == BrainState.AskToBringAnotherObject:
                newState = BrainState.Conversing
            elif self._state == BrainState.ObjectRecognised:
                newState = BrainState.PlayingVideo
                if not self._intent.playVideo(self._lockedObjectTarget.name):
                    newState = BrainState.FailedPlayingVideo
            elif self._state == BrainState.FailedPlayingVideo:
                self._intent.dontHaveVideo(self._lockedObjectTarget.name)
                newState = BrainState.Conversing
            elif self._state == BrainState.PlayingVideo:
                if not self._intent.isPlayingVideo():
                    self._intent.stopVideo()
                    newState = BrainState.Conversing
                    self._intent.askToBringAnotherObject()
        else:
            # Slowly getting more and more disengaged if no target
            self._timeToDissengaged -= 1
            self._timeToReleaseLockedObject -= 1

            if self._timeToReleaseLockedObject <= 0 and self._state == BrainState.ObjectRecognised:
                newState = BrainState.Conversing
                self._lockedObjectTarget = None

            if self._timeToDissengaged <= 0:
                # Run out of patience, not having a target for a very long time, change to idle state
                newState = BrainState.Idle
                # Reset this locked object so we can re-recognise again
                self._lockedObjectTarget = None

        if self._state != BrainState.Idle and self._currentTarget is not None:
            self._timeToDissengaged = self._DISSENGAGED_PATIENCE

        self._setState(newState)

    def _setState(self, newState):
        if newState != self._state:
            self._currentStateTime = Stopwatch()

        self._state = newState

    def _lockToTarget(self, targetTuple):
        self._currentTarget, self._currentTargetDistance = targetTuple

    def _releaseTarget(self):
        self._currentTarget = None
        self._currentTargetDistance = None

    def _updateEyePosition(self):
        if self._currentTarget is not None:
            # We need to transform from the object detection coordinate system into puppet eye coordinate system
            newEyeCenter = self._eyeCoordMapper.transform(self._currentTarget.getEyeCenter())
            # If we have eye target, then
            if self._currentEyeCenter is None:
                # If we don't have previous eye position, just update with the new one instantly
                self._currentEyeCenter = newEyeCenter
            else:
                # Else gaze slowly to the new position (using damping factor) so the eye do not flicker when the
                # detected person bounding box shifted/flicker
                curEyeCenter = self._currentEyeCenter.scale(self._EYE_MOVEMENT_SMOOTHING_FACTOR)
                newEyeCenter = newEyeCenter.scale(1.0 - self._EYE_MOVEMENT_SMOOTHING_FACTOR)

                self._currentEyeCenter = curEyeCenter.add(newEyeCenter)

            # As we have target, we slowly increasing eye target weight to overtake the eye fidget movement
            self._currentTargetFocusWeight = min(1.0, self._currentTargetFocusWeight + self._FOCUS_EYE_SPEED)
            self._noEyeTargetTimer = 0
        else:
            self._noEyeTargetTimer += 1
            if self._noEyeTargetTimer > self._NO_EYE_TARGET_PATIENCE:
                # No eye target, we slowly decreasing eye target weight to let eye fidget movement to take priority
                self._currentTargetFocusWeight = max(0.0, self._currentTargetFocusWeight - self._FOCUS_EYE_SPEED)

                # If we are totally disengaged or idle, reset eye center to None
                if self._currentTargetFocusWeight <= 0.0 or self._state == BrainState.Idle:
                    self._currentEyeCenter = None

    def update(self, lastFrameCaptured):
        if self._isSetupReady:
            print("Setup ready!")
            self._updateEyeTarget(lastFrameCaptured)
            self._updateObjectTarget(lastFrameCaptured)
            self._updateBrainState()
            self._updateEyePosition()
        else:
            self._startCtr += 1
            maxScale = Config.frameScale(100)
            print("StartCtr {0} aiming {1}".format(self._startCtr, maxScale))
            if self._startCtr > maxScale:
                self._intent = Intent()
                self._isSetupReady = True


    def _getPersonToEngage(self, lastFrameCaptured):
        targetToEngaged = None
        targetDistance = None
        # Find human in the lastFrameCaptured and if we have already an engaged target, stick to that as much as possible
        # so we don't alternate between person very frequently if both are close to each other
        if self._currentTarget is not None:
            # Find this target first if still there in the lastFrameCaptured
            targetToEngaged, targetDistance = lastFrameCaptured.findExistingObject(self._currentTarget)

        # Cannot find existing target to engage, try to find a new one
        if targetToEngaged is None and lastFrameCaptured is not None:
            targetToEngaged, targetDistance = lastFrameCaptured.findNewObject()

        return targetToEngaged, targetDistance

    def getState(self):
        return self.state

    def getEyeTargetParam(self):
        if self._isSetupReady:
            return self._currentEyeCenter, self._currentTargetFocusWeight
        return None, None
