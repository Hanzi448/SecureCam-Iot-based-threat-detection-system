import cv2
from ml.yolo_wrapper import YOLOv8Detector

def run_webcam_detection():
    print("Starting YOLOv8 webcam detection...")

    # Initialize YOLOv8 model
    detector = YOLOv8Detector(
        model_path="models/yolo/best.pt",
        names_path="models/yolo/obj.names"
    )
    print("YOLOv8 model loaded successfully!")

    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return

    print("Webcam opened. Press 'q' to quit.\n")

    last_detections = []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Run YOLO detection
        detections = detector.predict(frame)

        current_detections = []

        # Draw and print detections
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            conf = det["conf"]
            label = det["label"]
            current_detections.append(f"{label} ({conf:.2f})")

            # Draw boxes and labels on the frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} ({conf:.2f})", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Print only if there are new detections
        if current_detections != last_detections:
            if current_detections:
                for obj in current_detections:
                    print(f"Detected: {obj}")
            else:
                print("No objects detected.")
            last_detections = current_detections

        # Show the frame
        cv2.imshow("YOLOv8 - Webcam Detection", frame)

        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\nDetection stopped by user.")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_webcam_detection()
