import os
import cv2
import numpy as np
from config import Config

if Config.ENABLE_TF:
    import tensorflow as tf
    from tfutils import visualization_utils as vis_util
    from tfutils import label_map_util

from PIL import Image, ImageDraw

from utilities.jsonFile import JsonFile
from utilities.rectArea import RectArea
from utilities.vector import Vector


def gstreamer_pipeline(
    capture_width=720,
    capture_height=540,
    display_width=360,
    display_height=270,
    framerate=5,
    flip_method=0,
):
    return (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

class ObjectName(object):
    Person = "person"


class ObjectCaptured(object):
    _MIN_PERSON_LENGTH = 5 / 100   # 5% of screen width
    _MIN_OBJ_LENGTH = 5 / 100 # 5% of screen width

    def __init__(self, name, boundingBox, confScore):
        self.name = name
        self.boundingBox = boundingBox
        self.confScore = confScore

    def getEstimatedDistance(self):
        # Distance is the inverse of bounding box length
        return 1.0 / self.boundingBox.length()

    def getEyeCenter(self):
        return Vector(self.boundingBox.center()[0], self.boundingBox.y1 + self.boundingBox.height() * 0.1)

    def isBigEnough(self):
        if self.name == ObjectName.Person and self.boundingBox.length() >= self._MIN_PERSON_LENGTH:
            return True

        if self.boundingBox.length() >= self._MIN_OBJ_LENGTH:
            return True

        return False


class FrameCaptured(object):

    def __init__(self):
        self._objects = []

    def addObject(self, objCaptured):
        self._objects.append(objCaptured)

    def findExistingObject(self, existingObj, objectName=ObjectName.Person, exclusionNames={}):
        for obj in self._objects:
            if objectName is not None and obj.name != objectName:
                continue
            if obj.name in exclusionNames:
                continue
            if existingObj.boundingBox.isOverlap(obj.boundingBox):
                return obj, obj.getEstimatedDistance()

        return None, None

    def findNewObject(self, objectName=ObjectName.Person, exclusionNames={}):
        for obj in self._objects:
            if objectName is not None and obj.name != objectName:
                continue
            if obj.name in exclusionNames:
                continue
            if obj.isBigEnough():
                return obj, obj.getEstimatedDistance()

        return None, None


class ObjectDetection(object):

    def __init__(self):
        self._cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
        self._lastFrameCaptured = None
        self._ctr = 0       
        if self._cap.isOpened():
            print("Successfully open camera source")
            self._windowHandle = cv2.namedWindow("Camera", cv2.WINDOW_AUTOSIZE)

        self._setup()

    def _setup(self):
        MODEL_NAME = 'toys-4-class-jetsoncam'
        LABELS = 'labels.pbtxt'

        CWD_PATH = os.getcwd()

        PATH_TO_CKPT = os.path.join(CWD_PATH, MODEL_NAME, 'frozen_inference_graph.pb')

        detection_graph = tf.compat.v1.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

            self._TFSess = tf.compat.v1.Session(graph=detection_graph)

        self._image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

        self._detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

        self._detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
        self._detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')

        self._num_detections = detection_graph.get_tensor_by_name('num_detections:0')

        labelMapFilePath = os.path.join(CWD_PATH, MODEL_NAME, LABELS.split(".")[0] + ".txt")

        with open(labelMapFilePath, "r") as f:
            txt = f.read()
            self._labels = txt.split("\n")

    def _update(self):
        minScore = 0.4
        ret_val, frame = self._cap.read()
        print("Got video frame {0}".format(frame.shape))

        width = frame.shape[1]
        height = frame.shape[0]

        frame.setflags(write=1)
        frame_expanded = np.expand_dims(frame, axis=0)

        (boxes, scores, classes, num) = self._TFSess.run(
            [self._detection_boxes, self._detection_scores, self._detection_classes, self._num_detections],
            feed_dict={self._image_tensor: frame_expanded})

        boxesList = np.squeeze(boxes).tolist()
        scores = np.squeeze(scores).tolist()
        classes = np.squeeze(classes).astype(np.int32).tolist()

        objList = []

        for i, box in enumerate(boxesList):
            score = scores[i]
            if score < minScore:
                continue

            classIdx = classes[i] - 1
            label = self._labels[classIdx]
            x1 = int(box[1] * width)
            y1 = int(box[0] * height)
            x2 = int(box[3] * width)
            y2 = int(box[2] * height)
            objList.append({"class": label, "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}, "score": score})

        self._lastFrameCaptured = FrameCaptured()

        for obj in objList:
            x1 = 1.0 - obj['box']['x1'] / width
            y1 = 1.0 - obj['box']['y1'] / height
            x2 = 1.0 - obj['box']['x2'] / width
            y2 = 1.0 - obj['box']['y2'] / height
            objName = obj['class']
            if objName == 'face':
                objName = ObjectName.Person

            self._lastFrameCaptured.addObject(ObjectCaptured(objName, RectArea(x1, y1, x2, y2), obj['score']))

        cv2.imshow("Camera", frame)

    def getLastFrameCaptured(self):
        self._update()
        return self._lastFrameCaptured

    def findExistingObject(self, existingObj):
        return self._lastFrameCaptured.findExistingObject(existingObj)

    def findNewObject(self):
        return self._lastFrameCaptured.findNewObject()


class ObjectDetectionOffline(object):

    def __init__(self, movieFilePath, objDetectCacheFolder):
        self._cap = cv2.VideoCapture(movieFilePath)
        self._objDetectCacheFolder = objDetectCacheFolder
        self._lastFrameCaptured = None
        self._ctr = -1
        self._frameCtr = 0
        self._speedFactor = 1
        if self._cap.isOpened():
            print("Successfully open camera source")
            self._windowHandle = cv2.namedWindow("Camera", cv2.WINDOW_AUTOSIZE)

    def _readOfflineCache(self, ctr):
        filePath = os.path.join(self._objDetectCacheFolder, "frame-{0:04}.txt".format(ctr))
        jsonObj = JsonFile.jsonFromFile(filePath)

        return jsonObj

    def _update(self):
        self._ctr += 1

        ret_val, img = self._cap.read()
        print("Got video frame {0}".format(img.shape))
        cv2.imshow("Camera", img)
        width = img.shape[1]
        height = img.shape[0]

        self._lastFrameCaptured = FrameCaptured()

        jsonObj = self._readOfflineCache(self._frameCtr)

        for obj in jsonObj['objects']:
            x1 = obj['box']['x1'] / width
            y1 = 1.0 - obj['box']['y1'] / height
            x2 = obj['box']['x2'] / width
            y2 = 1.0 - obj['box']['y2'] / height
            objName = obj['class']
            if objName == 'face':
                objName = ObjectName.Person

            self._lastFrameCaptured.addObject(ObjectCaptured(objName, RectArea(x1, y1, x2, y2), obj['score']))
        self._frameCtr += 1

    def getLastFrameCaptured(self):
        self._update()
        return self._lastFrameCaptured

    def findExistingObject(self, existingObj):
        return self._lastFrameCaptured.findExistingObject(existingObj)

    def findNewObject(self):
        return self._lastFrameCaptured.findNewObject()


class ObjectDetectionFake(object):

    def __init__(self):
        self._lastFrameCaptured = None
        self._ctr = 0

    def _update(self):
        self._lastFrameCaptured = FrameCaptured()

        self._ctr += 1
        mod = self._ctr % 2500

        # Simulate seeing a person at these locations
        if mod < 250:
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.0, 0.0, 0.1, 0.1), 0.9))
        elif mod < 500:
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.9, 0.9, 1.0, 1.0), 0.9))
        elif mod < 750:
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.9, 0.0, 1.0, 0.1), 0.9))
        elif mod < 1500:
        # Simulate seeing a person and a horse
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.0, 0.9, 0.1, 1.0), 0.9))
            self._lastFrameCaptured.addObject(ObjectCaptured("Horse", RectArea(0.0, 0.9, 0.1, 1.0), 0.9))
        elif mod < 1900:
            # Simulate seeing a person and a giraffe
            self._lastFrameCaptured.addObject(ObjectCaptured(ObjectName.Person, RectArea(0.0, 0.9, 0.1, 1.0), 0.9))
            self._lastFrameCaptured.addObject(ObjectCaptured("Giraffe", RectArea(0.0, 0.9, 0.1, 1.0), 0.9))
        else:
            pass


    def getLastFrameCaptured(self):
        self._update()
        return self._lastFrameCaptured

    def findExistingObject(self, existingObj):
        return self._lastFrameCaptured.findExistingObject(existingObj)

    def findNewObject(self):
        return self._lastFrameCaptured.findNewObject()
