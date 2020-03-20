import os
import boto3
import hashlib

from audio import Audio
from utilities.fileSearch import FileSearch


class Speech(object):
    _YOUR_AWS_KEY = "" # Enter your aws key here
    _YOUR_AWS_SECRET = "" # Enter your aws secret here

    def __init__(self, audioFolder):
        self._audio = Audio()
        self._audioFolder = audioFolder
        audioFilePathList = FileSearch.collectFilesEndsWithNameRecursively(".ogg", audioFolder)

        self._cache = {}
        for path in audioFilePathList:
            fileName = path.split("/")[-1].split(".")[0]
            self._cache[fileName] = path

        self._pollyClient = boto3.Session(
                        aws_access_key_id=self._YOUR_AWS_KEY,
                        aws_secret_access_key=self._YOUR_AWS_SECRET,
                        region_name='ap-southeast-2').client('polly')

    def speak(self, text):
        if len(self._YOUR_AWS_KEY) == 0 or len(self._YOUR_AWS_SECRET) == 0:
            return

        hashObject = hashlib.sha1(text.encode())
        hash = hashObject.hexdigest()

        if hash in self._cache:
            audioFilePath = self._cache[hash]
        else:
            audioFilePath = self._tts(text, hash)

        self._cache[hash] = audioFilePath

        self._audio.play(audioFilePath)


    def isSpeaking(self):
        return self._audio.isPlaying()

    def isAfterSpeaking(self):
        return self._audio.isAfterPlaying()

    def _tts(self, text, hash):
        response = self._pollyClient.synthesize_speech(VoiceId='Ivy',
                        OutputFormat='mp3',
                        Text = text)
        filePath = os.path.join(self._audioFolder, "{0}.mp3".format(hash))
        file = open(filePath, 'wb')
        file.write(response['AudioStream'].read())
        file.close()

        return filePath
