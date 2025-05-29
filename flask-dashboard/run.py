from flask import Flask
from controllers import *
from websocket import socketio

def create_app():
    app = Flask(__name__)

    app.register_blueprint(OverviewBlueprint)
    app.register_blueprint(AlertsBlueprint)
    app.register_blueprint(DroneBlueprint)
    app.register_blueprint(DeviceDetailsBlueprint)

    socketio.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)