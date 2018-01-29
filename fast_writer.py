# import the necessary packages
from imutils.video import FileVideoStream
from imutils.video.pivideostream import PiVideoStream
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import imutils
import time
import cv2


def main(args):
    # created a *threaded *video stream, allow the camera sensor to warmup,
    # and start the FPS counter
    print("[INFO] warming up camera...")
    vs = PiVideoStream().start()
    time.sleep(2.0)

    # initialize the FourCC, video writer, dimensions of the frame, and
    # zeros array
    fourcc = cv2.VideoWriter_fourcc(*args["codec"])
    writer = None
    (h, w) = (None, None)
    length = args["length"]
    temp = list()
    counter = 0
    timeframe = 0

    # loop over some frames...this time using the threaded stream
    while True:
        # grab the frame from the threaded video stream and resize it
        # to have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        if writer is None:
            # store the image dimensions, initialzie the video writer,
            # and construct the zeros array
            (h, w) = frame.shape[:2]
            writer = cv2.VideoWriter(args["output"] + "_" + str(timeframe), fourcc, args["fps"],
                                     (w, h), True)

        # check to see if the frame should be displayed to our screen
        if args["display"] > 0:
            cv2.imshow("Frame", frame)

        temp.append(frame)
        counter += 1
        if counter >= args["fps"]:
            for img in temp:
                writer.write(img)
            temp = list()
            counter = 0
            timeframe = (timeframe + 1) % length
            writer.release()
            writer = cv2.VideoWriter(args["output"] + "_" + str(timeframe) + ".avi",
                                     fourcc, args["fps"], (w, h), True)

        key = cv2.waitKey(1) & 0xFF
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            if counter and counter < length - 1:
                for img in temp:
                    writer.write(img)
                for i in range(length - 1 - counter):
                    writer.write(temp[counter - 1])
            break

    print("[INFO] cleaning up...")
    cv2.destroyAllWindows()
    vs.stop()
    writer.release()
    print("[INFO] saving...")
    writer = cv2.VideoWriter(args["output"] + ".avi",
                             fourcc, args["fps"], (w, h), True)
    summary(args["output"], timeframe, length, writer)
    writer.release()


def summary(name, timeframe, length, writer):
    for i in range(length):
        idx = (length + timeframe - i) % length if i > timeframe else (timeframe - i) % length
        fvs = FileVideoStream(name + "_" + str(idx) + ".avi")
        print(name + "_" + str(idx) + ".avi")
        while fvs.more():
            frame = fvs.read()
            frame = imutils.resize(frame, width=400)
            print("hey")
            cv2.imshow("Frame", frame)
            writer.write(frame)
        fvs.stop()


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
    parser.add_argument("-l", "--length", type=int, default=5,
                        help="length of seconds of summary")
    parser.add_argument("-d", "--display", type=int, default=-1,
                        help="Whether or not frames should be displayed")

    args = vars(parser.parse_args())

    main(args)
