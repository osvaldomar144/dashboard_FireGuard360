from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Cambia con una chiave segreta unica per la sicurezza

# Funzione per connettersi a MySQL
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="my-secret-pw",
        database="fireguard_db",
        port=3306
    )
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connessione al database
        conn = get_db_connection()
        cur = conn.cursor()

        # Recupera l'utente dal database
        cur.execute('SELECT * FROM utenti WHERE username = %s;', (username,))
        user = cur.fetchone()

        # Controllo delle credenziali
        if user and check_password_hash(user[2], password):  # user[2] è la password_hash
            session['user_id'] = user[0]  # Salva l'ID dell'utente nella sessione
            return redirect(url_for('index'))  # Redirige alla homepage
        cur.close()
        conn.close()
        return 'Credenziali errate, riprova.', 403  # Messaggio di errore per credenziali sbagliate

    return render_template('login.html')

@app.route('/')
def index():
    if 'user_id' not in session:  # Verifica se l'utente è loggato
        return redirect(url_for('login'))  # Redirige alla pagina di login se non è loggato

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

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Rimuove l'ID dell'utente dalla sessione
    return redirect(url_for('login'))  # Redirige alla pagina di login

if __name__ == "__main__":
    app.run(debug=True)