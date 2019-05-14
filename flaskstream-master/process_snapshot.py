#!/usr/bin/env python3

import sys
import cv2
from vision.image_analyzer import ImageAnalyzer


def main(file):
    print(file)
    frame = cv2.imread(file)
    _, stats, processed_image, _ = ImageAnalyzer.run(frame, "front")
    print(stats)
    cv2.imshow("Processed image for #{file}", processed_image)
    cv2.waitKey()

if __name__ == "__main__":
    main(sys.argv[1])
