#!/usr/bin/env bash
python video_writer.py --output ~/Videos/test.avi --picamera 1
python motion_detect.py --video ~/Videos/test.avi
