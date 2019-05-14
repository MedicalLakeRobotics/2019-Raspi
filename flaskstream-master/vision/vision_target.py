import numpy as np
import cv2
import math

#TODO:  Memoize where appropriate!

ANGLE_ERROR_FACTOR = 10.0

class VisionTarget:
    def __init__(self, contour):
        self.contour = contour
        self.rotated_rectangle = cv2.minAreaRect(contour)

    def bounding_box_aspect_ratio(self):
        x, y, w, h = self.bounding_rectangle()
        return float(w) / h

    def bounding_rectangle(self):
        return cv2.boundingRect(self.contour)

    def area(self):
        return cv2.contourArea(self.contour)

    def moments(self):
        return cv2.moments(self.contour)

    def center_point(self):
        m = self.moments()
        x = int(m["m10"] / m["m00"]) if m["m00"] != 0 else 0
        y = int(m["m01"] / m["m00"]) if m["m00"] != 0 else 0
        return (x, y)

    def top_y_value(self):
        c = self.contour
        if c is None:
            print("Contour missing - can't compute top y")
            return None
        y = tuple(c[c[:, :, 1].argmin()][0])[1]
        return y

    def rotated_rectangle_points(self):
        box = cv2.boxPoints(self.rotated_rectangle)
        box = np.intp(box)
        return [box]

    def rotation_angle(self):
        return self.rotated_rectangle[2]

    def angle_from_vertical(self):
        points = self.rotated_rectangle_points()[0]
        dp1_2 = self.distance_between_points(points[0], points[1])
        dp2_3 = self.distance_between_points(points[1], points[2])
        if dp2_3 > dp1_2:
            p1 = points[1]
            p2 = points[2]
        else:
            p1 = points[0]
            p2 = points[1]
        # the angle (degrees from vertical) = arctan(abs(p2y - p1y)/abs(p2x - p1x))
        xdelta = abs(float(p2[0] - p1[0]))
        if xdelta == 0.0:
            theta = 0.0
        else:
            theta = 90.0 - math.degrees(math.atan(abs(p2[1] - p1[1]) / xdelta))
        #if slope is negative, then the angle is returned as negative
        if p1[0] > p2[0]:
            return theta * -1.0
        return theta

    def distance_between_points(self, point1, point2):
        x1 = point1[0]
        x2 = point2[0]
        y1 = point1[1]
        y2 = point2[1]
        dx = x2 - x1
        dy = y2 - y1
        distance =  math.sqrt(dx ** 2 + dy ** 2)
        return distance

    def rotated_rectangle_center(self):
        return self.rotated_rectangle[0]

    def rotated_rectangle_dimensions(self):
        return self.rotated_rectangle[1]

    def is_potential_left_target(self):
        theta = self.angle_from_vertical()
        if theta > (14.5 + ANGLE_ERROR_FACTOR):
            return False
        if theta < (14.5 - ANGLE_ERROR_FACTOR):
            return False
        return True

    def is_potential_matching_right_target(self, left_target):

        theta = self.angle_from_vertical()
        if theta > (-14.5 + ANGLE_ERROR_FACTOR):
            return False
        if theta < (-14.5 - ANGLE_ERROR_FACTOR):
            return False
        lx, ly, lw, lh = left_target.bounding_rectangle()
        rx, ry, rw, rh = self.bounding_rectangle()
        if rx < (lx + lw): return False  # right can't be more leftward than the right edge of the left target
        if ry > (ly + lh): return False  # right can't be completely below left
        if (ry + rh) < ly: return False  # right can't be completely above left
        return True

    def report(self):
        lines = []
        lines.append("-------VISION TARGET--------")
        lines.append("Area: {}".format(self.area()))
        lines.append("Moments: {}".format(self.moments))
        lines.append("Center (from moments): {}".format(self.center_point()))
        lines.append("Rotation from vertical: {}".format(self.angle_from_vertical()))
        lines.append("RotRec center: {}".format(self.rotated_rectangle_center()))
        lines.append("RotRec dimensions: {}".format(self.rotated_rectangle_dimensions()))
        lines.append("RotRec points: {}".format(self.rotated_rectangle_points()))
        lines.append("Potential left target: {}".format(self.is_potential_left_target()))
        lines.append("-----------------------------")
        return lines
