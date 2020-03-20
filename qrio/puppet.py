import arcade
import time

from config import Config
from robot import Robot
from morphTarget import MorphTarget
from utilities.vector import Vector
from animation import Animation
from objectDetection import ObjectDetectionOffline, ObjectDetection, ObjectDetectionFake
from utilities.fpsCalc import FpsCalc


class MyGame(arcade.Window):
    """ Main application class. """

    def __init__(self, width, height):
        super().__init__(width, height)

        arcade.set_background_color(arcade.color.WHITE)
        self._width = width
        self._height = height
        self._fpsCalc = FpsCalc()

    def setup(self):
        movieFilePath = "/Users/agustinus.nalwan/Desktop/Work/AI/Dev/Personal/Qnabot/code/testVideo/footage-toys.mp4"
        objDetectCacheFolder = "/Users/agustinus.nalwan/Desktop/Work/AI/Dev/Personal/Qnabot/code/testVideo/objDetect/footage-toys"

        if Config.OBJECT_DETECTION == "live":
            self._objectDetection = ObjectDetection()
        elif Config.OBJECT_DETECTION == "fake":
            self._objectDetection = ObjectDetectionFake()
        elif Config.OBJECT_DETECTION == "offline":
            self._objectDetection = ObjectDetectionOffline(movieFilePath=movieFilePath, objDetectCacheFolder=objDetectCacheFolder)

        self._robot = Robot((self._width, self._height))

        # self._paramVec = Vector(0.0, 0.0)
        # self._targetParamVec = Vector(0.0, 0.0)

        #TODO: Testing the eye target animation using a timer animation. Remove this code when we
        #already replace with vector containing location of face from object detection
        # self._animateParamVectorTo(Vector(0.0, -0.5), 0.05)

    # def _animateParamVectorTo(self, newVector, speed):
    #     self._animation = Animation(newVector, speed)

    def on_draw(self):
        """ Render the screen. """
        arcade.start_render()
        # Your drawing code goes here
        self._robot.spriteList().draw()
        # arcade.glEnable(arcade.GL_TEXTURE_2D)
        # arcade.glTexParameteri(arcade.GL_TEXTURE_2D, arcade.GL_TEXTURE_MIN_FILTER, arcade.GL_NEAREST)
        # arcade.glTexParameteri(arcade.GL_TEXTURE_2D, arcade.GL_TEXTURE_MAG_FILTER, arcade.GL_NEAREST)

    def update(self, delta_time):
        if Config.SLEEP > 0:
            time.sleep(Config.SLEEP)

        """ All the logic to move, and the game logic goes here. """
        # print(delta_time)
        lastFrameCaptured = self._objectDetection.getLastFrameCaptured()
        print("FPS: {0:.1f}".format(self._fpsCalc.log()))
        self._robot.update(lastFrameCaptured)
        # if self._animation.update():
        #     self._animateParamVectorTo(Vector(0.0, -0.5), 0.02)
            # sound = Sound('speech.ogg')
            # playstat=sound.play()
            # while True:
            #     time.sleep(1)
            #     print(sound.player._players[0].time)
            # pass

def main():
    game = MyGame(Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
