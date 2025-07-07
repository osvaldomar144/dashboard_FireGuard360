from flask import Blueprint, render_template
from flask_login import login_required
from utility.db import exec_stored_procedure

blp = Blueprint("drone", __name__, url_prefix='/drone')

@blp.route('/')
@login_required
def index():
    result = exec_stored_procedure("get_latest_system_danger", [1])
    danger_level = result[0]['danger_level'] if result else 0
    return render_template('drone/drone.html', danger_level=danger_level)