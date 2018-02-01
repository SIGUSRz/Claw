import cv2

cap = cv2.VideoCapture(0)
cv2.namedWindow('frame', cv2.WINDOW_NORMAL)

while(True):
    ret, frame = cap.read()
    cv2.imshow('frame', frame)
    key = cv2.waitKey(5)
    if key == ord('q'):
        break
cv2.destroyAllWindows()