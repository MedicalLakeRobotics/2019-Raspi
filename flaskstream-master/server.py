#!/usr/bin/env python3
from flask import Flask, render_template, Response
from robot import Robot
import time

app = Flask(__name__)
robot = Robot()
robot.startup()
print(robot.front_camera)
print(robot.rear_camera)
print(robot.live_camera)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    return Response(generate_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=--frame')

def generate_stream():
    while True:
        time.sleep(robot.frame_lag)
        frame = robot.live_camera.get_frame()
        size = len(frame)
        prefix = "--frame\r\nContent-Type: image/jpeg\r\nContent-length: {}\r\n\r\n".format(size).encode('utf-8')
        yield prefix + frame + b'\r\n'

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
