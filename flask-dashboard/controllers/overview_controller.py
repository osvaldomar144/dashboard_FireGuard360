from flask import Blueprint, render_template
from flask_login import login_required

blp = Blueprint("overview", __name__, url_prefix='/overview')

@blp.route('/')
@login_required
def index():
    # Esempio dati mock per test
    alert_rows = [
        {'Timestamp': '2025-06-01 14:23', 'Descrizione': 'Fumo rilevato nella Zona A'},
        {'Timestamp': '2025-06-01 13:58', 'Descrizione': 'Temperatura anomala rilevata'},
        {'Timestamp': '2025-06-01 13:10', 'Descrizione': 'Allarme manuale attivato'},
        {'Timestamp': '2025-06-01 13:10', 'Descrizione': 'Allarme manuale attivato'},
        {'Timestamp': '2025-06-01 13:10', 'Descrizione': 'Allarme manuale attivato'},
        {'Timestamp': '2025-06-01 13:10', 'Descrizione': 'Allarme manuale attivato'},
        {'Timestamp': '2025-06-01 13:10', 'Descrizione': 'Allarme manuale attivato'},
        {'Timestamp': '2025-06-01 13:10', 'Descrizione': 'Allarme manuale attivato'},
        {'Timestamp': '2025-06-01 13:10', 'Descrizione': 'Allarme manuale attivato'},
        {'Timestamp': '2025-06-01 13:10', 'Descrizione': 'Allarme manuale attivato'},
        {'Timestamp': '2025-06-01 13:10', 'Descrizione': 'Allarme manuale attivato'}
    ]
    return render_template('overview/index.html', alert_rows=alert_rows)