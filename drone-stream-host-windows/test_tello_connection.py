from djitellopy import Tello

try:
    drone = Tello()
    print("[INFO] Connessione al drone...")
    drone.connect(wait_for_state=True)

    battery = drone.get_battery()
    print(f"[INFO] Batteria drone: {battery}%")

    print("[INFO] Avvio streaming video...")
    drone.streamon()
    frame = drone.get_frame_read().frame

    if frame is not None:
        print("[INFO] Frame ricevuto correttamente.")
    else:
        print("[WARN] Nessun frame ricevuto.")

    drone.streamoff()
    drone.end()

except Exception as e:
    print(f"[ERRORE] {e}")
