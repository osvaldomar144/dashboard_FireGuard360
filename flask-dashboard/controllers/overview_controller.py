from flask import Blueprint, render_template
from flask_login import login_required

blp = Blueprint("overview", __name__, url_prefix='/overview')

@blp.route('/')
@login_required
def index():
    return render_template('overview/index.html')