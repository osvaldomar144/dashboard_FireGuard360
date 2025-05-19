from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    from dotenv import load_dotenv
    import os

    load_dotenv(dotenv_path="CONFIG_FIREGUARD360.env")

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_URL = os.getenv("DB_URL").replace("jdbc:mysql://", "")

    DB_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_URL}"

    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
