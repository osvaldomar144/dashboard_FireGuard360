from flask import Blueprint, render_template
from flask_login import login_required

blp = Blueprint("drone", __name__, url_prefix='/drone')

@blp.route('/')
@login_required
def index():
    return render_template('drone/drone.html')