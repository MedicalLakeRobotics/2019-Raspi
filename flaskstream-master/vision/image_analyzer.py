import cv2
import numpy as np
from vision.image_processing_pipeline import ImageProcessingPipeline
from vision.target_analyzer import TargetAnalyzer
from vision.vision_target import VisionTarget

class ImageAnalyzer:
    @classmethod
    def run(cls, image, position):
        analyzer = ImageAnalyzer(image, position)
        return analyzer.execute()

    def __init__(self, image, position):
        self.image = image
        self.original_image = np.copy(self.image)
        self.position = position
        self.height, self.width = self.image.shape[:2]
        self.center_x = int(self.width / 2)

    def execute(self):
        #manipulates a copy of the image to find potential vision targets in the image
        candidate_targets, img = ImageProcessingPipeline(self.image).run()

        #analyzes candidate targets to find either a matching set of targets, or None
        target_analyzer = TargetAnalyzer(candidate_targets, self.width, self.height)
        target_analyzer.execute()
        target_analyzer.report()
        stats = target_analyzer.stats()

        #Draw a centerline and any matching targets on the image
        self.draw_centerline()
        target_analyzer.draw_targets(self.image)

        return self.original_image, stats, img, self.image

    def draw_centerline(self):
        cv2.line(self.image, (self.center_x, 0), (self.center_x, self.height - 1), (255, 255, 255), 2)
