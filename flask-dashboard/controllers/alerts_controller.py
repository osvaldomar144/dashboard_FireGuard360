from flask import Blueprint, render_template
from flask_login import login_required

from utility.db import exec_stored_procedure

blp = Blueprint("alerts", __name__, url_prefix='/alerts')

@blp.route('/')
@login_required
def index():
    alert_rows = exec_stored_procedure("get_latest_fire_alerts", [100])

    alert_rows = [
        {**alert, 'timestamp': alert['timestamp'].strftime('%Y-%m-%d %H:%M') if alert.get('timestamp') else None} 
        for alert in alert_rows
    ]
    return render_template('alerts/alerts.html', alert_rows=alert_rows)