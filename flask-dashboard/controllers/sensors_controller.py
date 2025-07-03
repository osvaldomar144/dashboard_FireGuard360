from flask import Blueprint, render_template
from flask_login import login_required

from utility.db import exec_stored_procedure

blp = Blueprint("sensors", __name__, url_prefix='/sensors')

@blp.route('/')
@login_required
def index():
    sensors_rows = exec_stored_procedure("get_raw_sensor_data", [None, None, None])

    sensors_rows = [
        {**sensor, 'detected_at': sensor['detected_at'].strftime('%Y-%m-%d %H:%M') if sensor.get('detected_at') else None} 
        for sensor in sensors_rows
    ]
    return render_template('sensors/sensors.html', sensors_rows=sensors_rows)