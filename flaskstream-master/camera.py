import yaml
import subprocess
import os
import sys
import time
from datetime import datetime
import threading
import cv2
import numpy as np
from vision.image_analyzer import ImageAnalyzer

try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class CameraEvent(object):
    """Used to keep track of threading states for each camera object"""
    def __init__(self):
        self.events = {}

    def wait(self):
        """Invoked by each client's thread to wait for the next frame"""
        ident = get_ident()
        if ident not in self.events:
            self.events[ident] = [threading.Event(), time.time()]
            return self.events[ident][0].wait()

    def set(self):
        """Invoked by the client's thread whenever a new frame is available"""
        now = time.time()
        remove = None
        for ident, event in self.events.items():
            if not event[0].isSet():  #the client's event is not set, so set it
                event[0].set()
                event[1] = now
            else:  #client didn't process a prior frame - if persists for more than 5 sec, assume client is dead
                if now - event[1] > 5:
                    remove = ident

        if remove:
            del self.events[remove]

    def clear(self):
        """Invoiced from client's thread after a frame is processed"""
        self.events[get_ident()][0].clear()


class RobotCamera:
    """Encapsulates a camera used for both vision processing and driving video"""

    def __init__(self, robot, linux_device, camera_index, role, serial_number):
        self.robot = robot
        self.linux_device = linux_device
        self.camera_index = camera_index
        self.role = role
        self.serial_number = serial_number
        self.height = 240
        self.width = 320
        self.fps = 15
        self.thread = None
        self.frame = None
        self.event = CameraEvent()

    def start_streaming(self):
        self._init_thread()

    def get_frame(self):
        self.event.wait()
        self.event.clear()
        return self.frame

    def _init_thread(self):
        if self.thread is None:
            #start up the background thread for opencv frame processing
            self.thread = threading.Thread(target=self._thread)
            self.thread.start()

            #wait until a frame comes through
            while self.get_frame() is None:
                time.sleep(0)

    def _thread(self):
        frames_iterator = self.frames()
        for frame in frames_iterator:
            self.frame = frame
            self.event.set()
            time.sleep(0)

        self.thread = None

    def frames(self):
        camera = self._get_opencv_camera()
        if not camera.isOpened():
            raise RuntimeError("Could not start camera {}".format(self.linux_device))

        quality_params = [int(cv2.IMWRITE_JPEG_QUALITY), self.robot.jpeg_quality]
        while True:
            try:
                raw_frame, processed_frame, final_frame = self._process_frame(camera)

                stream_frame = cv2.resize(final_frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
                if self.robot.flip_image:
                    stream_frame = cv2.flip(stream_frame, 1)
                yield cv2.imencode('.jpg', stream_frame, quality_params)[1].tobytes()
                if self.robot.take_snapshot_now == True:
                    self._save_snapshot(raw_frame, "raw")
                    self._save_snapshot(processed_frame, "processed")
                    self.robot.take_snapshot_now = False
            except:
                print("unable to grab frame from camera")


    def _save_snapshot(self, frame, frametype):
        filename = "../snapshots/snapshot-{}-{}.jpg".format(datetime.now().strftime("%Y%m%d-%H%M%S"), frametype)
        cv2.imwrite(filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    #returns raw_frame, processed_frame, final_frame
    def _process_frame(self, camera):
        processed_img = None
        _, frame = camera.read()
        try:
            if self.role == "front":
                #Perform OpenCV vision analysis here!
                original_image, stats, processed_img, img_to_stream = ImageAnalyzer.run(frame, self.role)
                self.robot.send_stats_to_robot(stats, self)
                img = img_to_stream
            else:
                img = frame
                original_image = frame
            return original_image, processed_img, img
        except Exception as error:
            print(error)
            print("exception in _process_frame")
            return frame, None, frame

    def _get_opencv_camera(self):
        ndx = int(self.camera_index)
        props = {
            'brightness': 145,
            'gain': 68,
            'exposure_auto': 1,  #manual
            'exposure_absolute': 60,
            'contrast': 112,
            'white_balance_temperature_auto': 0 #off
        }
        self._set_camera_properties(props)
        self._set_fps(self.fps)

        subprocess.call(['v4l2-ctl -d /dev/video1 -l'], shell=True)
        camera = cv2.VideoCapture(ndx)

        #set camera resolution
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        return camera

    def _set_fps(self, fps):
        subprocess.call(['v4l2-ctl -d /dev/video{} -p {}'.format(self.camera_index, fps)],shell=True)

    def _set_camera_properties(self, camera_properties_hash):
        for key in camera_properties_hash:
            subprocess.call(['v4l2-ctl -d /dev/video{} -c {}={}'.format(self.camera_index, key, str(camera_properties_hash[key]))],shell=True)
