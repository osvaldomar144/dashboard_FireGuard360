from flask import Blueprint, render_template

blp = Blueprint("device", __name__, url_prefix='/device')

@blp.route('/')
def index():
    return render_template('device_details/device_details.html')