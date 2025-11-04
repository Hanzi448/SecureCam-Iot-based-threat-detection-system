import cv2

url = "http://192.168.137.157"
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("❌ Could not open ESP32 stream.")
else:
    print("✅ ESP32 stream opened successfully!")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Frame not received.")
            continue
        cv2.imshow("ESP32 Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
