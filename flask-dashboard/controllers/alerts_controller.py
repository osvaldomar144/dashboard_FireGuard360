from flask import Blueprint, render_template
from flask_login import login_required

blp = Blueprint("alerts", __name__, url_prefix='/alerts')

@blp.route('/')
@login_required
def index():
    return render_template('alerts/alerts.html')