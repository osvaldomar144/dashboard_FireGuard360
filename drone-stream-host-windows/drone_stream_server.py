import cv2
import time
import threading
from flask import Flask, Response
from ultralytics import YOLO
import numpy as np
from djitellopy import Tello
import os
import traceback

# === CONFIG ===
# USE_SIMULATION = os.environ.get("USE_SIMULATION", "true").lower() == "true"
USE_SIMULATION = False
SIMULATION_SOURCE = os.environ.get("SIMULATION_SOURCE", "fire.mp4")
YOLO_MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "best.pt")
FRAME_WIDTH = int(os.environ.get("FRAME_WIDTH", 1280))
FRAME_HEIGHT = int(os.environ.get("FRAME_HEIGHT", 720))

# === VERIFICHE FILE NECESSARI ===
if USE_SIMULATION and not os.path.exists(SIMULATION_SOURCE):
    raise FileNotFoundError(f"[ERRORE] Sorgente video non trovata: {SIMULATION_SOURCE}")

if not os.path.exists(YOLO_MODEL_PATH):
    raise FileNotFoundError(f"[ERRORE] Modello YOLO non trovato: {YOLO_MODEL_PATH}")

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
        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            start_time = time.time()

            ret, frame = cap.read()
            if not ret:
                print("[WARN] Fine del video o webcam non disponibile.")
                break

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            frame = detect_objects(frame)

            with frame_lock:
                output_frame = frame.copy()

            elapsed = time.time() - start_time
            time.sleep(max(0, 1 / 30 - elapsed))

        cap.release()

    else:
        try:
            print("[INFO] Connessione al drone Tello in corso...")
            drone = Tello()
            print("[DEBUG] Inizio connessione Tello...")
            try:
                drone.connect()
                print("[DEBUG] Connessione riuscita.")
            except Exception as e:
                print("[DEBUG] Connessione fallita:", e)
            print(f"[INFO] Batteria: {drone.get_battery()}%")
            drone.streamon()
            cap = drone.get_frame_read()

            while True:
                start_time = time.time()

                frame = cap.frame
                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                frame = detect_objects(frame)

                with frame_lock:
                    output_frame = frame.copy()

                elapsed = time.time() - start_time
                time.sleep(max(0, 1 / 30 - elapsed))

        except Exception as e:
            print(f"[ERROR] Errore nella gestione del drone: {e}")
            traceback.print_exc()
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
    print("[INFO] Server Flask in esecuzione su http://0.0.0.0:5010")
    try:
        app.run(host="0.0.0.0", port=5010, debug=False)
    except KeyboardInterrupt:
        print("[INFO] Arresto del server richiesto.")
