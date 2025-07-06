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

def serialize_row(row):
    return {
        key: (value.strftime('%Y-%m-%d %H:%M') if isinstance(value, datetime.datetime) else value)
        for key, value in row.items()
    }

class OverviewNamespace(Namespace):
    def on_connect(self):
        global connected_clients, push_thread
        connected_clients += 1
        print(f"[WS] Client connesso a /alerts. Totale: {connected_clients}")

        if connected_clients == 1:
            # Primo client -> avvia il push
            print("[WS] Avvio del push periodico alerts.")
            stop_event.clear()
            push_thread = Thread(
                target=periodic_alert_push, 
                args=(current_app._get_current_object(),),
                daemon=True
            )
            push_thread.start()

    def on_disconnect(self):
        global connected_clients
        connected_clients -= 1
        print(f"[WS] Client disconnesso da /alerts. Totale: {connected_clients}")

        if connected_clients == 0:
            # Ultimo client -> stoppa il push
            print("[WS] Nessun client attivo. Fermata del push.")
            stop_event.set()

def periodic_alert_push(app):
    with app.app_context():
        while not stop_event.is_set():
            try:

                # 2. Ultimi allarmi
                alerts = exec_stored_procedure("get_latest_fire_alerts", [100])
                serialized_alerts = [serialize_row(a) for a in alerts]
                socketio.emit("update_alerts", serialized_alerts, namespace="/alerts")

            except Exception as e:
                print(f"[WS] Errore durante il push alerts: {e}")
            time.sleep(3)

# Registra il namespace
socketio.on_namespace(OverviewNamespace("/alerts"))