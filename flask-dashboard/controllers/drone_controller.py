from flask import Blueprint, render_template

blp = Blueprint("drone", __name__, url_prefix='/drone')

@blp.route('/')
def index():
    return render_template('drone/drone.html')