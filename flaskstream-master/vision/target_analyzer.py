import cv2
import numpy as np
import itertools
import math
from vision.vision_target import VisionTarget

CAMERA_FOV_WIDTH_DEGREES = 61.179  # CODED FOR LOGITECH C920 HORIZONTAL FOV (empirical)
CAMERA_FOV_HEIGHT_DEGREES = 43.3   # CODED FOR LOGITECH C922 VERTICAL FOV (specs)
TARGET_GAP_INCHES = 8.0           # From FRC manual
CAMERA_HEIGHT_INCHES = 50.2 #46.0
TARGET_HEIGHT_ROCKET_CARGO_INCHES = 39.125
TARGET_HEIGHT_STANDARD_INCHES = 31.5


class TargetAnalyzer:
    def __init__(self, candidate_targets, image_width, image_height):
        self.image_width = image_width
        self.image_height = image_height
        self.candidate_targets = candidate_targets
        self.left_target = None
        self.right_target = None
        self.target_center_x = None
        self.target_heading = None
        self.target_distance_from_target_gap = None
        self.target_distance_from_vertical = None
        self.target_distance_from_vertical_rocket_cargo = None
        self.success = False

    def execute(self):
        possible_matches = []
        for one, two in itertools.combinations(self.candidate_targets, 2):
            if self.check_for_match(one, two) == True:
                possible_matches.append((one, two))
            elif self.check_for_match(two, one) == True:
                possible_matches.append((two, one))

        if len(possible_matches) == 0:
            self.success = False
        else:
            best_match = self.best_match(possible_matches)
            self.left_target = best_match[0]
            self.right_target = best_match[1]
            if self.left_target == None or self.right_target == None:
                self.target_center_x = None
                self.target_heading = None
                self.target_distance_from_target_gap = None
                self.target_distance_from_vertical = None
                self.target_distance_from_vertical_rocket_cargo = None
                self.success = False
            else:
                self.target_center_x = self.target_pair_center_x()
                self.target_heading = self.calculate_heading()
                self.target_distance_from_target_gap = self.calculate_distance_from_target_gap()
                self.target_distance_from_vertical = self.calculate_distance_from_vertical(False)
                self.target_distance_from_vertical_rocket_cargo = self.calculate_distance_from_vertical(True)
                self.success = True

    def target_pair_center_x(self):
        lx, _ =  self.left_target.center_point()
        rx, _ = self.right_target.center_point()
        return int((rx + lx) / 2.0)

    def target_top_y(self):
        if self.left_target is None or self.right_target is None:
            return None
        y = self.left_target.top_y_value()
        y2 = self.right_target.top_y_value()
        if y2 < y:
            y = y2
        return y

    def calculate_heading(self):
        if self.left_target is None or self.right_target is None:
            return None
        target_x = self.target_pair_center_x()
        center_x = self.image_width / 2
        if target_x == center_x:
            return 0.0
        pixels_off = abs(center_x - target_x)
        heading_abs = CAMERA_FOV_WIDTH_DEGREES * float(pixels_off) / self.image_width
        if target_x < center_x:
            return heading_abs * -1.0
        else:
            return heading_abs

    def calculate_distance_from_target_gap(self):
        if self.left_target == None or self.right_target == None:
            return None
        left = self.left_target.rotated_rectangle_points()[0][3]   #inner top point on left target
        right = self.right_target.rotated_rectangle_points()[0][1] #inner top point on right target
        target_gap_pixels = right[0] - left[0]  #NOTE:  Should we use the point distance algorithm here, or is x-diff good enough?
        theta = CAMERA_FOV_WIDTH_DEGREES * target_gap_pixels / self.image_width # angle in degrees of target gap in picture
        distance_by_triangle = (TARGET_GAP_INCHES / 2) / math.tan(math.radians(theta / 2))
        return distance_by_triangle

    def calculate_distance_from_vertical(self, target_is_rocket_cargo):
        top_y = self.target_top_y()
        center_y = self.image_height / 2
        offset_in_pixels = center_y - top_y
        vertical_angle = (offset_in_pixels * CAMERA_FOV_HEIGHT_DEGREES) / self.image_height
        print("Pixel offset: {}".format(offset_in_pixels))
        print("vertical angle: {}".format(vertical_angle))
        if target_is_rocket_cargo == True:
            target_height = TARGET_HEIGHT_ROCKET_CARGO_INCHES
        else:
            target_height = TARGET_HEIGHT_STANDARD_INCHES

        inches_offset = abs(CAMERA_HEIGHT_INCHES - target_height)
        print("offset {} -- target height: {}".format(inches_offset, target_height))
        distance = abs(inches_offset / (math.tan(math.radians(vertical_angle))))
        return distance

    def best_match(self, possible_matches):
        if len(possible_matches) == 0:
            return (None, None)
        #TODO:  Replace this with code that can pick between multiple possible match pairs
        return possible_matches[0]

    def check_for_match(self, left, right):
        if not(left.is_potential_left_target()): return False
        if not(right.is_potential_matching_right_target(left)): return False
        return True

    def report(self, report_no_match=False):
        lines = []
        if self.success == True:
            lines.append("LEFT:")
            lines.append("None" if self.left_target == None else self.left_target.report())
            lines.append("RIGHT:")
            lines.append("None" if self.right_target == None else self.right_target.report())
            lines.append("Success: {}".format(self.success))
            lines.append("HEADING: {} degrees".format(self.target_heading))
            lines.append("DISTANCE (TARGET GAP): {} inches".format(self.target_distance_from_target_gap))
            lines.append("DISTANCE (VERTICAL - NORMAL): {} inches".format(self.target_distance_from_vertical))
            lines.append("DISTANCE (VERTICAL - ROCKET CARGO): {} inches".format(self.target_distance_from_vertical_rocket_cargo))
        else:
            if report_no_match:
                lines.append("NO MATCH")
        for line in lines:
            print(line)

    def stats(self):
        if self.success == True:
            return [self.success, self.target_pair_center_x(), self.target_top_y(), self.target_heading, self.target_distance_from_target_gap, self.target_distance_from_vertical_rocket_cargo, self.target_distance_from_vertical]
        else:
            return [self.success]

    def draw_targets(self, img):
        if self.success == True:
            for target in [self.left_target, self.right_target]:
                if target == None: continue

                #Draw the rotated rect around the targets
                cv2.drawContours(img, target.rotated_rectangle_points(), 0, (0,255,0), 5)

                #Draw a vertical line to show the center point between the two targets
                x = self.target_center_x
                cv2.line(img, (x, 0), (x, self.image_height - 1), (0, 255, 0), 2)

