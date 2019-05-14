#!/bin/bash

#install core prerequisites
sudo apt-get update
sudo apt-get install -y build-essential autoconf automake libtool pkg-config gtk-doc-tools libreadline-dev libncursesw5-dev libdaemon-dev libjson-glib-dev libglib2.0-dev vim
sudo apt-get install -y cmake pkg-config libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev
sudo apt-get install -y libx264-dev libgtk2.0-dev libgtk-3-dev libatlas-base-dev gfortran
sudo apt-get install -y python3-dev python3-pip git-core zip cmake

sudo pip3 install numpy scipy pyyaml flask

#install GStreamer libraries
sudo apt-get install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer1.0.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools

# OpenCV
mkdir ~/frc4513
mkdir ~/frc4513/sources
cd ~/frc4513/sources
wget -O opencv.zip https://github.com/opencv/opencv/archive/3.4.3.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/3.4.3.zip
unzip opencv.zip
unzip opencv_contrib.zip

cd ~/frc4513/sources/opencv-3.4.3/
mkdir build
cd build

cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D INSTALL_PYTHON_EXAMPLES=ON \
    -D OPENCV_EXTRA_MODULES_PATH=~/frc4513/sources/opencv_contrib-3.4.3/modules \
    -D BUILD_EXAMPLES=ON ..

make -j4

sudo make install
sudo ldconfig
sudo apt-get update

sudo reboot
