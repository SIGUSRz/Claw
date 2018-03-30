from imutils.video import VideoStream
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
    vs = VideoStream(usePiCamera=args["picamera"]).start()
    print("[INFO] warming up camera...")
    time.sleep(2.0)

    # initialize the FourCC, video writer, dimensions of the frame, and
    # zeros array
    temp = list()
    bucket = list()
    timeframe = 0
    counter = 0
    # kcw = KeyClipWriter(buf_size=args["fps"] * args["length"])
    cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
    params = {
        "name": "",
        "fourcc": cv2.VideoWriter_fourcc(*args["codec"]),
        "fps": args["fps"],
        "w": None,
        "h": None
    }
    writer = None

    # prefix = os.path.join(args["output"], out_name)
    # loop over some frames...this time using the threaded stream
    start = time.time()
    while True:
        # grab the frame from the threaded video stream and resize it
        # to have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        temp.append(frame)

        if time.time() - start > 1:
            timeframe = (timeframe + 1) % args["length"]
            if len(bucket) > args["length"]:
                x = bucket.pop(0)
                del x
            bucket.append(temp.copy())
            del temp
            temp = list()
            start = time.time()
        if not q.empty():
            flag = q.get()
            if flag == 0:
                if writer is not None:
                    writer.release()
                break
            print("Writing")
            params["name"] = "{}/result_{}.avi".format(args["output"], counter)
            (params["h"], params["w"]) = frame.shape[:2]
            writer = cv2.VideoWriter(params["name"], params["fourcc"],
                                     params["fps"], (params["w"], params["h"]), True)
            for i in bucket:
                for j in i:
                    writer.write(j)
            writer.release()
            counter += 1
            print("Done")
        if args["display"]:
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

    print("[INFO] cleaning up...")
    cv2.destroyAllWindows()
    vs.stop()
    print("[INFO] done")


def watcher(dis):
    while True:
        start = time.time()
        event = dis.next_event()
        if event.type == X.ButtonPress and (int(event.detail) in [1, 2, 3]):
            if time.time() - start > 10:
                q.put(1)
        elif event.type == X.KeyPress and event.detail == 24:
            q.put(0)
            break


if __name__ == "__main__":
    # construct the argument parse and parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", required=True,
                        help="path to output video directory")
    parser.add_argument("-p", "--picamera", type=bool,
                        help="whether or not the Raspberry Pi camera should be used")
    parser.add_argument("-f", "--fps", type=int, default=120,
                        help="FPS of output video")
    parser.add_argument("-c", "--codec", type=str, default="MJPG",
                        help="codec of output video")
    parser.add_argument("-t", "--type", type=str, default="avi",
                        help="video file type to save")
    parser.add_argument("-l", "--length", type=int, default=16,
                        help="length of seconds of summary")
    parser.add_argument("-d", "--display", type=bool,
                        help="Whether or not frames should be displayed")

    arg = vars(parser.parse_args())

    os.system("rm -rf %s" % arg["output"])
    os.makedirs(arg["output"])
    display = Display(':0')
    root = display.screen().root
    root.grab_pointer(True, X.ButtonPressMask | X.ButtonReleaseMask, X.GrabModeAsync,
                      X.GrabModeAsync, 0, 0, X.CurrentTime)
    root.grab_keyboard(True, X.GrabModeAsync, X.GrabModeAsync, X.CurrentTime)
    watcher_thread = Thread(target=watcher, args=(display,))
    main_thread = Thread(target=main, args=(arg,))
    watcher_thread.start()
    main_thread.start()
