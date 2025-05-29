from flask import Blueprint, render_template
from flask_login import login_required

blp = Blueprint("device", __name__, url_prefix='/device')

@blp.route('/')
@login_required
def index():
    return render_template('device_details/device_details.html')