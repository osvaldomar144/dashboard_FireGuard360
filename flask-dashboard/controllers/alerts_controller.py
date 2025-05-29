from flask import Blueprint, render_template

blp = Blueprint("alerts", __name__, url_prefix='/alerts')

@blp.route('/')
def index():
    return render_template('alerts/alerts.html')