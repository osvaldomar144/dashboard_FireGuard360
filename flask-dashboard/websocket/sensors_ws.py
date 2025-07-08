from flask import current_app, request
from flask_socketio import Namespace, emit
from .socketio import socketio
from utility.db import exec_stored_procedure
from threading import Thread, Event
from datetime import datetime
import time

connected_clients = 0
stop_event = Event()
push_thread = None

# Mappa socket ID → filtro attivo
filters_by_sid = {}

def serialize_row(row):
    return {
        key: (value.strftime('%Y-%m-%d %H:%M') if isinstance(value, datetime) else value)
        for key, value in row.items()
    }

def clean_datetime(value):
    """Converte stringa ISO in formato compatibile con MySQL"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "")).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return None

class OverviewNamespace(Namespace):
    def on_connect(self):
        global connected_clients, push_thread
        connected_clients += 1
        print(f"[WS] Client connesso a /sensors. Totale: {connected_clients}")

        if connected_clients == 1:
            print("[WS] Avvio del push periodico sensors.")
            stop_event.clear()
            push_thread = Thread(
                target=periodic_alert_push,
                args=(current_app._get_current_object(),),
                daemon=True
            )
            push_thread.start()

    def on_disconnect(self, sid):
        global connected_clients
        connected_clients -= 1
        filters_by_sid.pop(sid, None)
        print(f"[WS] Client disconnesso da /sensors. Totale: {connected_clients}")
        if connected_clients == 0:
            print("[WS] Nessun client attivo. Fermata del push.")
            stop_event.set()

    def on_update_filter(self, data):
        sid = request.sid
        print(f"[WS] Ricevuto filtro da {sid}: {data}")

        start_date = clean_datetime(data.get("start_date"))
        end_date = clean_datetime(data.get("end_date"))

        filters_by_sid[sid] = (start_date, end_date)

def periodic_alert_push(app):
    with app.app_context():
        while not stop_event.is_set():
            try:
                for sid, (start, end) in filters_by_sid.items():
                    # Dati grezzi (tabella)
                    sensors = exec_stored_procedure("get_raw_sensor_data", [None, start, end])
                    serialized_sensors = [serialize_row(a) for a in sensors]
                    socketio.emit("update_sensors", serialized_sensors, to=sid, namespace="/sensors")

                    # Dati aggregati (grafici)
                    stats = exec_stored_procedure("get_stats_for_charts", [None, None, None])
                    serialized_stats = [serialize_row(s) for s in stats]
                    print(f"serialized_stats: {serialized_stats}")
                    socketio.emit("update_stats", serialized_stats, to=sid, namespace="/sensors")

            except Exception as e:
                print(f"[WS] Errore durante il push sensors: {e}")

            time.sleep(3)

# Registra il namespace
socketio.on_namespace(OverviewNamespace("/sensors"))
