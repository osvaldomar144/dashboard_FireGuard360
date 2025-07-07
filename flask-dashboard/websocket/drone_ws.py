from flask import current_app
from flask_socketio import Namespace, emit
from .socketio import socketio
from utility.db import exec_stored_procedure
from threading import Thread, Event
import time
import datetime

connected_clients = 0
stop_event = Event()
push_thread = None
last_danger_level = None  # salva ultimo livello inviato

class OverviewNamespace(Namespace):
    def on_connect(self):
        global connected_clients, push_thread
        connected_clients += 1
        print(f"[WS] Client connesso a /drone. Totale: {connected_clients}")

        if connected_clients == 1:
            print("[WS] Avvio push realtime danger level.")
            stop_event.clear()
            push_thread = Thread(
                target=periodic_danger_push,
                args=(current_app._get_current_object(),),
                daemon=True
            )
            push_thread.start()

    def on_disconnect(self):
        global connected_clients
        connected_clients -= 1
        print(f"[WS] Client disconnesso da /drone. Totale: {connected_clients}")

        if connected_clients == 0:
            print("[WS] Nessun client attivo. Fermata push danger level.")
            stop_event.set()

def periodic_danger_push(app):
    global last_danger_level

    with app.app_context():
        while not stop_event.is_set():
            try:
                result = exec_stored_procedure("get_latest_system_danger", [1])
                if result:
                    level = result[0]["danger_level"]
                    print(f"Ecco il level nuovo ricevuto {level} ed ecco il vecchio {last_danger_level}")
                    if level != last_danger_level:
                        last_danger_level = level
                        socketio.emit("danger_level_update", {"danger_level": level}, namespace="/device")
            except Exception as e:
                print(f"[WS] Errore durante danger level push: {e}")
            time.sleep(3)

# Registra il namespace
socketio.on_namespace(OverviewNamespace("/drone"))
