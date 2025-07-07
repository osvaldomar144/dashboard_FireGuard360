from flask import Blueprint, render_template
from flask_login import login_required
from utility.db import exec_stored_procedure

blp = Blueprint("device", __name__, url_prefix='/device')

@blp.route('/')
@login_required
def index():
    result = exec_stored_procedure("get_latest_system_danger", [1])
    danger_level = result[0]['danger_level'] if result else 0

    return render_template('device_details/device_details.html', danger_level=danger_level)