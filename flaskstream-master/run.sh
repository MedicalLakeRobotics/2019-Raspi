#!/bin/sh

cd /home/nvidia/frc4513/flaskstream
FLASK_APP=server.py python3 -m flask run --port=1180 --host=0.0.0.0
