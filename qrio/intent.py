import os
import time

from speech import Speech
from config import Config

if Config.IS_JETSON:
    from browserServiceJetson import BrowserService
else:
    from browserServiceMac import BrowserService

from utilities.stopwatch import Stopwatch


class Intent(object):

    def __init__(self):
        self._speech = Speech("audio/")
        self._startPlayingVideoTime = None
        if Config.ENABLE_BROWSER:
            print("Initing browser intent")
            self._browserService = BrowserService()

    def isBusy(self):
        #TODO: Add a bit of delay to keep busy status 2 seconds after talking
        return self.isTalking() or self.isAfterTalking() or self.isPlayingVideo()

    def isTalking(self):
        return self._speech.isSpeaking()

    def isAfterTalking(self):
        return self._speech.isAfterSpeaking()

    def askToComeAndPlay(self):
        self._speech.speak("Hi Dexie? do you want to come and play?")

    def askToBringObject(self):
        self._speech.speak("Dexie? Do you want to bring me something?")

    def askToBringNewObject(self, oldObjectName):
        self._speech.speak("We have just played with {0} already. Why don'y you bring me something else?".format(self._appendObjectNameAbbreviation(oldObjectName)))

    def askToBringAnotherObject(self):
        self._speech.speak("Well, that was fun isn't it? Do you want to bring me something else?")

    def _appendObjectNameAbbreviation(self, objectName):
        objectName = objectName.lower()
        if objectName[0] in {'a', 'i', 'e', 'o', 'u'}:
            objectName = "an {0}".format(objectName)
        else:
            objectName = "a {0}".format(objectName)

        return objectName

    def dontHaveVideo(self, objectName):
        self._speech.speak("I am sorry. I cannot find a video about {0}! Do you want to bring me something else?".format(
            self._appendObjectNameAbbreviation(objectName)))

    def objectRecognised(self, objectName):
        self._speech.speak("Hey, I think that is {0}!".format(self._appendObjectNameAbbreviation(objectName)))

    def playVideo(self, objectName):
        ret = True
        self._speech.speak("Hang on a second. Let me play you a video about {0}!".format(self._appendObjectNameAbbreviation(objectName)))
        if Config.ENABLE_BROWSER:
            ret = self._browserService.searchAndPlay(objectName)

        if ret:
            self._startPlayingVideoTime = Stopwatch()

        return ret

    def isPlayingVideo(self):
        if self._startPlayingVideoTime is None:
            return False

        elapsedSec = self._startPlayingVideoTime.get() / 1000

        return elapsedSec < Config.VIDEO_PLAYBACK_TIME

    def stopVideo(self):
        if Config.ENABLE_BROWSER:
            self._browserService.stop()
