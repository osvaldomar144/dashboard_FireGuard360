from flask import Blueprint, send_from_directory
from flask import jsonify
from datetime import datetime
import os

SharedImagesBlueprint = Blueprint("SharedImagesBlueprint", __name__)

# Path nel container montato dal docker-compose
SHARED_FOLDER_PATH = "/app/shared"

@SharedImagesBlueprint.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(SHARED_FOLDER_PATH, filename)


@SharedImagesBlueprint.route("/finalize-analysis", methods=["POST"])
def finalize_analysis():
    folder = SHARED_FOLDER_PATH
    original_path = os.path.join(folder, "result.png")

    if not os.path.isfile(original_path):
        return jsonify({"error": "Immagine non trovata"}), 404

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"result_{timestamp}.png"
    new_path = os.path.join(folder, new_name)

    try:
        os.rename(original_path, new_path)
        return jsonify({"status": "success", "new_filename": new_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500