#!/usr/bin/env bash
cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules -D PYTHON_DEFAULT_EXECUTABLE=/home/pi/.virtualenvs/py3/bin/python3 -D WITH_FFMPEG=ON -D BUILD_EXAMPLES=ON ..
