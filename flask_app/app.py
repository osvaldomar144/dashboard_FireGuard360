from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# Funzione per connettersi a MySQL
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",        # Host del contenitore MySQL
        user="root",             # Nome utente di default per MySQL
        password="my-secret-pw", # password
        database="fireguard_db", # database creato
        port=3306               # La porta mappata su localhost (3306)
    )
    return conn

@app.route('/')
def index():
    # Connessione al database
    conn = get_db_connection()
    cur = conn.cursor()

    # Esecuzione della query per ottenere i dati (temperatura, umidità, fumo)
    cur.execute('SELECT * FROM dati_arduino;')  
    dati = cur.fetchall()  

    # Chiusura della connessione
    cur.close()
    conn.close()

    # Passa i dati al template
    return render_template('index.html', dati=dati)

if __name__ == "__main__":
    app.run(debug=True)