from imutils.video.pivideostream import PiVideoStream
from picamera.array import PiRGBArray
from picamera import PiCamera
from imutils.video.webcamvideostream import WebcamVideoStream
from Xlib.display import Display
from Xlib import X
from threading import Thread
from queue import Queue
import argparse
import imutils
import time
import cv2
import os

q = Queue()
out_name = "result"
buffer_name = "temp"


def main(args):
    # created a *threaded *video stream, allow the camera sensor to warmup,
    # and start the FPS counter
    vs = PiVideoStream().start() if args["picamera"] else WebcamVideoStream().start()
    print("[INFO] warming up camera...")
    time.sleep(2.0)

    if not os.path.isdir(args["buffer"]):
        os.makedirs(args["buffer"])
    if not os.path.isdir(args["output"]):
        os.makedirs(args["output"])

    # initialize the FourCC, video writer, dimensions of the frame, and
    # zeros array
    fourcc = cv2.VideoWriter_fourcc(*args["codec"])
    writer = None
    (h, w) = (None, None)
    length = args["length"]
    temp = list()
    counter = 0
    timeframe = 0
    cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
    params = {
        "output": args["output"],
        "buffer": args["buffer"],
        "type": args["type"],
        "length": length,
        "fps": args["fps"],
        "counter": 0,
        "temp": None,
        "frame": None,
        "writer": None,
        "idx": 0,
        "res_code": 0
    }

    buffer_prefix = os.path.join(args["buffer"], buffer_name)
    # loop over some frames...this time using the threaded stream
    while True:
        # grab the frame from the threaded video stream and resize it
        # to have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)

        if params["writer"] is None:
            # store the image dimensions, initialzie the video writer,
            # and construct the zeros array
            (h, w) = frame.shape[:2]
            params["writer"] = cv2.VideoWriter(buffer_prefix + "_" +
                                               str(timeframe) + "." + args["type"],
                                               fourcc, args["fps"], (w, h), True)

        temp.append(frame)
        counter += 1
        params["counter"] = counter
        params["temp"] = temp
        params["frame"] = frame
        if counter >= args["fps"]:
            for img in temp:
                params["writer"].write(img)
            temp = list()
            counter = 0
            timeframe = (timeframe + 1) % length
            params["timeframe"] = timeframe
            params["writer"].release()
            params["writer"] = cv2.VideoWriter(buffer_prefix + "_" +
                                               str(timeframe) + "." + args["type"],
                                               fourcc, args["fps"], (w, h), True)

        if not q.empty():
            flag = q.get()
            if flag == 0:
                params["writer"].release()
                break
            click(params)

        # check to see if the frame should be displayed to our screen
        if args["display"]:
            cv2.imshow("Frame", frame)

    print("[INFO] cleaning up...")
    cv2.destroyAllWindows()
    vs.stop()
    print("[INFO] done")


def watcher(dis):
    while True:
        start = time.time()
        event = dis.next_event()
        if event.type == X.ButtonPress and event.detail == 1:
            if time.time() - start > 5:
                q.put(1)
                print(q.empty())
        elif event.type == X.KeyPress and event.detail == 24:
            q.put(0)
            break


def click(params):
    if params["counter"] != params["fps"] - 1 and params["writer"] is not None:
        for img in params["temp"]:
            params["writer"].write(img)
        for i in range(len(params["temp"]), params["fps"]):
            params["writer"].write(params["frame"])
    params["writer"].release()
    summary(params)


def summary(params):
    print("[INFO] saving...")
    buffer_prefix = os.path.join(params["buffer"], buffer_name)
    target = '"concat:'
    for i in range(params["length"] - 1, -1, -1):
        idx = (params["length"] + params["timeframe"] - i) % params["length"] \
            if i > params["timeframe"] else (params["timeframe"] - i) % params["length"]
        target += buffer_prefix + "_" + str(idx) + ".%s|" % params["type"]
    target = target.rstrip("|") + '"'
    command = "ffmpeg -y -i %s -c copy %s_%d.avi" % \
              (target, os.path.join(params["output"], out_name), params["res_code"])
    params["res_code"] += 1
    os.system(command)
    print("[INFO] saved")


if __name__ == "__main__":
    # construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=True,
                        help="path to output video directory")
    parser.add_argument("-b", "--buffer", required=True,
                        help="path to buffer directory")
    parser.add_argument("-p", "--picamera", type=bool,
                        help="whether or not the Raspberry Pi camera should be used")
    parser.add_argument("-f", "--fps", type=int, default=30,
                        help="FPS of output video")
    parser.add_argument("-c", "--codec", type=str, default="MJPG",
                        help="codec of output video")
    parser.add_argument("-t", "--type", type=str, default="avi",
                        help="video file type to save")
    parser.add_argument("-l", "--length", type=int, default=30,
                        help="length of seconds of summary")
    parser.add_argument("-d", "--display", type=bool,
                        help="Whether or not frames should be displayed")

    arg = vars(parser.parse_args())

    os.system("rm -rf %s" % arg["output"])
    os.system("rm -rf %s" % arg["buffer"])
    os.makedirs(arg["output"])
    os.makedirs(arg["buffer"])
    display = Display(':0')
    root = display.screen().root
    root.grab_pointer(True, X.ButtonPressMask | X.ButtonReleaseMask, X.GrabModeAsync,
                      X.GrabModeAsync, 0, 0, X.CurrentTime)
    root.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)
    watcher_thread = Thread(target=watcher, args=(display, ))
    main_thread = Thread(target=main, args=(arg, ))
    watcher_thread.start()
    main_thread.start()

