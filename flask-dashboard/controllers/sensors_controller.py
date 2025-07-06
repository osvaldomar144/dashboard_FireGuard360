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

    temp_data = {
        "labels": [
            "2025-07-03 12:00", 
            "2025-07-03 12:02", 
            "2025-07-03 12:04", 
            "2025-07-03 12:06",
            "2025-07-03 12:08", 
            "2025-07-03 12:10", 
            "2025-07-03 12:12",
        ],
        "datasets": [
            {
                "label": "Server1",
                "data": [27.5, 27.8, 27.1, 28.0, 27.9, 27.5, 27.8],
                "borderColor": "rgba(255, 99, 132, 1)",
                "tension": 0.3,
                "fill": False
            },
            {
                "label": "Server2",
                "data": [27.4, 27.7, 27.0, 27.9, 27.8, 27.9, 27.9],
                "borderColor": "rgba(54, 162, 235, 1)",
                "tension": 0.3,
                "fill": False
            }
        ]
    }

    hum_data = {
        "labels": [
            "2025-07-03 12:00", 
            "2025-07-03 12:02", 
            "2025-07-03 12:04", 
            "2025-07-03 12:06",
            "2025-07-03 12:08", 
            "2025-07-03 12:10", 
            "2025-07-03 12:12",
        ],
        "datasets": [
            {
                "label": "Server1",
                "data": [34.5, 33.8, 34.1, 33.0, 33.9, 33.8, 33.7],
                "borderColor": "rgba(255, 99, 132, 1)",
                "tension": 0.3,
                "fill": False
            },
            {
                "label": "Server2",
                "data": [33.4, 33.7, 34.0, 34.9, 34.8, 34.7, 34.6],
                "borderColor": "rgba(54, 162, 235, 1)",
                "tension": 0.3,
                "fill": False
            }
        ]
    }

    gas_data = {
        "labels": [
            "2025-07-03 12:00", 
            "2025-07-03 12:02", 
            "2025-07-03 12:04", 
            "2025-07-03 12:06",
            "2025-07-03 12:08", 
            "2025-07-03 12:10", 
            "2025-07-03 12:12",
        ],
        "datasets": [
            {
                "label": "Server1",
                "data": [280, 285, 282, 290, 300, 302, 300],
                "borderColor": "rgba(255, 99, 132, 1)",
                "tension": 0.3,
                "fill": False
            },
            {
                "label": "Server2",
                "data": [280, 290, 295, 290, 300, 298, 296],
                "borderColor": "rgba(54, 162, 235, 1)",
                "tension": 0.3,
                "fill": False
            }
        ]
    }

    return render_template('sensors/sensors.html', sensors_rows=sensors_rows, temp_data=temp_data, hum_data=hum_data, gas_data=gas_data)