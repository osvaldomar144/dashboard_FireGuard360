from flask import Blueprint, render_template

blp = Blueprint("overview", __name__, url_prefix='/overview')

@blp.route('/')
def index():
    return render_template('overview/index.html')