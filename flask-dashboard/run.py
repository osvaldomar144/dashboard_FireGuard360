from flask import Flask
from controllers import *
from websocket import socketio

from flask_login import LoginManager
from auth.routes import auth_bp

from utility.db import init_db

def create_app():
    app = Flask(__name__)
    app.secret_key = "fireguard360secretKey"

    # Inizializza il DB
    init_db(app)

    # Auth setup
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from utility.auth_utils import get_user_by_id
        return get_user_by_id(user_id)

    # Blueprint routes
    app.register_blueprint(OverviewBlueprint)
    app.register_blueprint(AlertsBlueprint)
    app.register_blueprint(DroneBlueprint)
    app.register_blueprint(DeviceDetailsBlueprint)
    app.register_blueprint(auth_bp)

    socketio.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)