from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# Funzione per connettersi a MySQL
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",        # Host del contenitore MySQL
        user="root",             # Nome utente di default per MySQL
        password="my-secret-pw", # La password che hai impostato
        database="fireguard_db", # Il database che hai creato
        port=3306               # La porta mappata su localhost (3307)
    )
    return conn

@app.route('/')
def index():
    # Connessione al database
    conn = get_db_connection()
    cur = conn.cursor()

    # Esegui una query per ottenere i dati (temperatura, umidità, fumo)
    cur.execute('SELECT * FROM dati_arduino;')  # Puoi aggiungere altre query qui
    dati = cur.fetchall()  # Ottieni tutti i dati dalla tabella

    # Chiudi la connessione
    cur.close()
    conn.close()

    # Passa i dati al template
    return render_template('index.html', dati=dati)

if __name__ == "__main__":
    app.run(debug=True)