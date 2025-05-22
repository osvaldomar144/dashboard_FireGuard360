from flask import Flask, render_template, request
from flask_socketio import SocketIO
from threading import Lock
from datetime import datetime
from sqlalchemy import text

from db import db, init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'donsky!'
socketio = SocketIO(app, cors_allowed_origins='*')


# Inizializza il database
init_db(app)

# Thread setup
thread = None
thread_lock = Lock()

def background_thread():
    with app.app_context():
        while True:
            try:
                with db.engine.connect() as connection:
                    result = connection.execute(text("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1"))
                    row = result.fetchone()

                    if row:
                        print(f"[DEBUG] Latest data found: sensor_id={row.sensor_id}, temperature={row.temperature}, timestamp={row.timestamp}")
                        data = {
                            "sensor_id": row.sensor_id,
                            "temperature": float(row.temperature),
                            "humidity": float(row.humidity),
                            "gas": float(row.gas),
                            "date": row.timestamp.strftime("%m/%d/%Y %H:%M:%S")
                        }
                        socketio.emit('updateSensorData', data)
                    else:
                        print("[DEBUG] No data found in DB")

            except Exception as e:
                print(f"[ERROR] Failed to query DB: {e}")

            socketio.sleep(1)


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True, debug=True)