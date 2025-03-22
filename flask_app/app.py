from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Cambia con una chiave segreta sicura

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

        # Recupera l'utenza dal database
        cur.execute('SELECT id, username, password_hash sword FROM utenti WHERE username = %s;', (username,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        # Controllo delle credenziali in modo sicuro (con hashing)
        if user and user[2] == password: 
            session['user_id'] = user[0]           # Salva l'ID utente nella sessione
            session['username'] = user[1]          # Salva il nome utente nella sessione
            return redirect(url_for('index'))      # Reindirizza alla homepage
        else:
            return 'Credenziali errate, riprova.', 403  # Messaggio di errore per credenziali sbagliate

    return render_template('login.html')

@app.route('/')
def index():
    if 'user_id' not in session:  # Verifica se l'utente è loggato
        return redirect(url_for('login'))  # Reindirizza al login se non loggato

    # Connessione al database per recuperare i dati Arduino
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM dati_arduino ORDER BY id DESC LIMIT 1;')  # Prendi solo l'ultimo record
    dati = cur.fetchall()

    cur.close()
    conn.close()

    # Passa i dati e il nome utente al template
    return render_template('index.html', dati=dati, username=session.get('username'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)     # Rimuove user_id
    session.pop('username', None)    # Rimuove username
    return redirect(url_for('login'))  # Torna al login

if __name__ == "__main__":
    app.run(debug=True)