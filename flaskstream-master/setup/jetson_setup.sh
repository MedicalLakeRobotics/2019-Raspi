#!/bin/bash

### Remove all old opencv stuffs installed by JetPack (or OpenCV4Tegra)
sudo apt-get purge libopencv*
### I prefer using newer version of numpy (installed with pip), so
### I'd remove this python-numpy apt package as well
sudo apt-get purge python-numpy
### Remove other unused apt packages
sudo apt autoremove
### Upgrade all installed apt packages to the latest versions (optional)
sudo apt-get update

### Update gcc apt package to the latest version (highly recommended)
sudo apt-get install -y --only-upgrade g++-5 cpp-5 gcc-5 gtk-doc-tools
### Install dependencies based on the Jetson Installing OpenCV Guide
sudo apt-get install -y build-essential make cmake cmake-curses-gui \
                       g++ libavformat-dev libavutil-dev \
                       libswscale-dev libv4l-dev libeigen3-dev \
                       libglew-dev libgtk2.0-dev pkg-config autoconf automake
### Install dependencies for gstreamer stuffs
sudo apt-get install -y libdc1394-22-dev libxine2-dev \
                       libgstreamer1.0-dev ibgstreamer1.0.0\
                       libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools
### Install additional dependencies according to the pyimageresearch
### article
sudo apt-get install -y libjpeg8-dev libjpeg-turbo8-dev libtiff5-dev \
                       libjasper-dev libpng12-dev libavcodec-dev json-glib-1.0 libjson-glib-dev libreadline-dev libncurses5-dev
sudo apt-get install -y libxvidcore-dev libx264-dev libgtk-3-dev \
                       libatlas-base-dev gfortran
sudo apt-get install -y libopenblas-dev liblapack-dev liblapacke-dev
### Install Qt5 dependencies
sudo apt-get install -y qt5-default
### Install dependencies for python3
sudo apt-get install -y python3-dev python3-pip python3-tk
sudo pip3 install numpy
sudo pip3 install flask pyyaml

mkdir ~/frc4513/sources
cd ~/frc4513/sources

# OpenCV
wget -O opencv.zip https://github.com/opencv/opencv/archive/3.4.3.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/3.4.3.zip
unzip opencv.zip
unzip opencv_contrib.zip

cd ~/frc4513/sources/opencv-3.4.3/
mkdir build
cd build

cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D WITH_CUDA=ON -D CUDA_ARCH_BIN="6.2" -D CUDA_ARCH_PTX="" \
        -D WITH_CUBLAS=ON -D ENABLE_FAST_MATH=ON -D CUDA_FAST_MATH=ON \
        -D ENABLE_NEON=ON -D WITH_LIBV4L=ON -D BUILD_TESTS=OFF \
        -D BUILD_PERF_TESTS=OFF -D BUILD_EXAMPLES=OFF \
        -D WITH_QT=ON -D WITH_OPENGL=ON \
        -D INSTALL_PYTHON_EXAMPLES=ON \
        -D OPENCV_EXTRA_MODULES_PATH=~/frc4513/sources/opencv_contrib-3.4.3/modules \
        -D BUILD_EXAMPLES=ON ..

make -j4
sudo make install

sudo reboot
