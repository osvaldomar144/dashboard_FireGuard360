from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
import os

db = SQLAlchemy()


def init_db(app):
    """
    Inizializza la connessione al DB e configura SQLAlchemy con Flask.
    """
    load_dotenv(dotenv_path="CONFIG_FIREGUARD360.env")

    DB_URI = os.getenv("SQLALCHEMY_DB_URI")
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)


def exec_stored_procedure(name, params=None):
    """
    Esegue una stored procedure MySQL con eventuali parametri.
    
    :param name: Nome della stored procedure.
    :param params: Lista o tupla di parametri (posizionali).
    :return: Lista di dizionari con i risultati (se ci sono).
    """
    if params is None:
        params = []

    sql = f"CALL {name}({', '.join([':p' + str(i) for i in range(len(params))])})"
    bind_params = {f"p{i}": p for i, p in enumerate(params)}

    with db.engine.connect() as connection:
        result = connection.execute(text(sql), bind_params)
        if result.returns_rows:
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]  # compatibile con SQLAlchemy 2.x
        return []
