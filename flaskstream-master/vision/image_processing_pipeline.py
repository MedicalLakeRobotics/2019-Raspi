import numpy as np;
import cv2;
from vision.vision_target import VisionTarget

ANALYSIS_PIPELINE = """
gaussian_blur
rgb_filter 0 255 218 255 0 255
erode 2
dilate 2
"""

MIN_AREA = 75
MAX_AREA = 60000
MIN_ASPECT_RATIO = 0.1
MAX_ASPECT_RATIO = 0.8

class ImageProcessingPipeline:
    def __init__(self, image):
        self.image = image

    #returns a list of potential messaing targets found in the manipulated image
    def run(self):
        img = self.image.copy()  # we do this so we don't muck up the original image
        pipeline = ANALYSIS_PIPELINE.splitlines()

        for cmd in pipeline:
            img = self.run_pipeline_step(img, cmd)

        return (self.find_potential_targets(img), img)

    def run_pipeline_step(self, img, cmd):
        cmds = cmd.split(" ")
        command = cmds.pop(0).strip()
        command_fn = self.get_function_for(command.upper())
        return command_fn(img, cmds)

    def get_function_for(self, command):
        if command == "BGR2HSL":
            return self.convert_bgr2hsl
        elif command == "BGR2GRAY":
            return self.convert_bgr2gray
        elif command == "GAUSSIAN_BLUR":
            return self.gaussian_blur
        elif command == "BINARY_THRESHOLD":
            return self.binary_threshold
        elif command == "ERODE":
            return self.erode
        elif command == "DILATE":
            return self.dilate
        elif command == "HSL_FILTER":
            return self.apply_hsl_filter
        elif command == "HSV_FILTER":
            return self.apply_hsv_filter
        elif command == "RGB_FILTER":
            return self.apply_rgb_filter
        return self.noop

    def noop(self, img, args):
        return img

    def apply_hsl_filter(self, img, args):
        hsl = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
        lower = (int(args[0]), int(args[2]), int(args[4]))
        upper = (int(args[1]), int(args[3]), int(args[5]))
        mask = cv2.inRange(hsl, lower, upper)
        return mask

    def apply_rgb_filter(self, img, args):
        hsl = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        lower = (int(args[0]), int(args[2]), int(args[4]))
        upper = (int(args[1]), int(args[3]), int(args[5]))
        mask = cv2.inRange(hsl, lower, upper)
        return mask

    def apply_hsv_filter(self, img, args):
        hsl = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = (int(args[0]), int(args[2]), int(args[4]))
        upper = (int(args[1]), int(args[3]), int(args[5]))
        mask = cv2.inRange(hsl, lower, upper)
        return mask

    def convert_bgr2hsl(self, img, args):
        return cv2.cvtColor(img, cv2.COLOR_BGR2HLS)

    def convert_bgr2gray(self, img, args):
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def gaussian_blur(self, img, args):
        return cv2.GaussianBlur(img, (5, 5), 0)

    def binary_threshold(self, img, args):
        min = int(args[0])
        max = int(args[1])
        return cv2.threshold(img, min, max, cv2.THRESH_BINARY)[1]

    def erode(self, img, args):
        iterations = int(args[0])
        return cv2.erode(img, None, iterations=iterations)

    def dilate(self, img, args):
        iterations = int(args[0])
        return cv2.dilate(img, None, iterations=iterations)

    def find_potential_targets(self, img):
        img, contours, _ = cv2.findContours(img,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        return self.filter_and_encapsulate_contours(contours)

    #this is more of a pre-filter - we're only removing things that are obviously too small or the aspect ratio of the bounding rect is way off
    #and we return the VisionTarget (which encapsulates the contour)
    def filter_and_encapsulate_contours(self, contours):
        targets = []
        for c in contours:
            target = VisionTarget(c)
            if target.area() < MIN_AREA:
                #print("Rejected contour - area too small")
                continue
            if target.area() > MAX_AREA:
                #print("Rejected contour - area too large")
                continue
            aspect_ratio = target.bounding_box_aspect_ratio()
            if aspect_ratio > MAX_ASPECT_RATIO or aspect_ratio < MIN_ASPECT_RATIO:
                #print("Rejected countour - aspect_ratio of {} is outside params".format(aspect_ratio))
                continue
            targets.append(target)
        return targets
