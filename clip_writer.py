# import the necessary packages
from __future__ import print_function
from imutils.video import VideoStream
import numpy as np
import argparse
import imutils
import time
import cv2


def main(args):
    # initialize the video stream and allow the camera
    # sensor to warmup
    print("[INFO] warming up camera...")
    vs = VideoStream(usePiCamera=args["picamera"] > 0).start()
    time.sleep(2.0)

    # initialize the FourCC, video writer, dimensions of the frame, and
    # zeros array
    fourcc = cv2.VideoWriter_fourcc(*args["codec"])
    writer = None
    (h, w) = (None, None)
    length = 30
    temp = list()
    pointer = 0
    timeframe = 0

    # loop over frames from the video stream
    while True:
        # grab the frame from the video stream and resize it to have a
        # maximum width of 300 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=500)

        # check if the writer is None
        if writer is None:
            # store the image dimensions, initialzie the video writer,
            # and construct the zeros array
            (h, w) = frame.shape[:2]
            writer = cv2.VideoWriter(args["output"] + "_" + str(timeframe), fourcc, args["fps"],
                                     (w, h), True)

        temp.append(frame)
        pointer += 1
        if pointer >= args["fps"]:
            for img in temp:
                writer.write(img)
            temp = list()
            pointer = 0
            timeframe = (timeframe + 1) % length
            writer.release()
            writer = cv2.VideoWriter(args["output"] + "_" + str(timeframe) + ".avi", fourcc, args["fps"],
                                     (w, h), True)

        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            if pointer and pointer < length - 1:
                for img in temp:
                    writer.write(img)
                for i in range(length - 1 - pointer):
                    writer.write(temp[pointer - 1])
            break

    # do a bit of cleanup
    print("[INFO] cleaning up...")
    cv2.destroyAllWindows()
    vs.stop()
    writer.release()


if __name__ == "__main__":
    # construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=True,
                        help="path to output video file")
    parser.add_argument("-p", "--picamera", type=int, default=-1,
                        help="whether or not the Raspberry Pi camera should be used")
    parser.add_argument("-f", "--fps", type=int, default=30,
                        help="FPS of output video")
    parser.add_argument("-c", "--codec", type=str, default="MJPG",
                        help="codec of output video")
    args = vars(parser.parse_args())

    main(args)
