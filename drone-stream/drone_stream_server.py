import cv2
import time
import threading
from flask import Flask, Response
from ultralytics import YOLO
import numpy as np
from djitellopy import Tello
import os

# === CONFIG ===
USE_SIMULATION = os.environ.get("USE_SIMULATION", "true").lower() == "true"
SIMULATION_SOURCE = 'fire.mp4'
YOLO_MODEL_PATH = "best.pt"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# === INIZIALIZZAZIONE MODELLO YOLO ===
model = YOLO(YOLO_MODEL_PATH)

# === STREAMING ===
app = Flask(__name__)
frame_lock = threading.Lock()
output_frame = None


def detect_objects(frame):
    """Esegue la detection e disegna i bounding box."""
    results = model.predict(source=frame, conf=0.5, verbose=False)
    if results and results[0].boxes and results[0].boxes.xyxy is not None:
        for box in results[0].boxes.xyxy:
            x1, y1, x2, y2 = box.int().tolist()
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return frame


def stream_frames():
    global output_frame

    if USE_SIMULATION:
        print("[INFO] Modalità SIMULAZIONE attiva.")
        cap = cv2.VideoCapture(SIMULATION_SOURCE)
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Fine del video o webcam non disponibile.")
                break
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            frame = detect_objects(frame)

            with frame_lock:
                output_frame = frame.copy()

            time.sleep(0.03)

        cap.release()

    else:
        try:
            print("[INFO] Connessione al drone Tello in corso...")
            drone = Tello()
            drone.connect()
            print(f"[INFO] Batteria: {drone.get_battery()}%")
            drone.streamon()
            cap = drone.get_frame_read()

            while True:
                frame = cap.frame
                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                frame = detect_objects(frame)

                with frame_lock:
                    output_frame = frame.copy()

                time.sleep(0.03)
        except Exception as e:
            print(f"[ERROR] Errore nella gestione del drone: {e}")
        finally:
            if 'drone' in locals():
                drone.streamoff()
                drone.end()


def generate_stream():
    global output_frame
    while True:
        with frame_lock:
            if output_frame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
            if not flag:
                continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               bytearray(encodedImage) +
               b"\r\n")


@app.route("/video_feed")
def video_feed():
    return Response(generate_stream(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/")
def index():
    return "<h1>Drone Video Feed</h1><img src='/video_feed' width='640' height='480'>"


if __name__ == "__main__":
    t = threading.Thread(target=stream_frames)
    t.daemon = True
    t.start()
    print("[INFO] Server Flask in esecuzione su http://0.0.0.0:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
