from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
        cur.execute('SELECT id, username, password_hash FROM utenti WHERE username = %s;', (username,))
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
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Connessione al database per recuperare tutti i dati Arduino
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM dati_arduino ORDER BY data_ora DESC;')  # Ordina per data_ora decrescente
    dati = cur.fetchall()

    cur.close()
    conn.close()

    # Passa i dati al template (non è più necessario passare i dati dei grafici qui)
    return render_template('index.html', username=session.get('username'))

# Nuova rotta per restituire i dati in formato JSON per l'aggiornamento dinamico
@app.route('/get_data')
def get_data():
    # Connessione al database per recuperare tutti i dati Arduino
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM dati_arduino ORDER BY data_ora DESC;')  # Ordina per data_ora decrescente
    dati = cur.fetchall()

    cur.close()
    conn.close()

    # Prepara i dati per il grafico in formato JSON
    data = [{
        "temperatura": row[1],
        "umidita": row[2],
        "fumo": row[3],
        "data_ora": row[4].strftime("%Y-%m-%d %H:%M:%S")
    } for row in dati]

    # Restituisci i dati in formato JSON
    return jsonify(data)

@app.route('/get_data_filter', methods=['GET'])
def get_filtered_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Debug: stampa le date ricevute
    print(f"Start Date: {start_date}")
    print(f"End Date: {end_date}")

    # Connessione al database per recuperare i dati filtrati in base al range di date
    conn = get_db_connection()
    cur = conn.cursor()

    # Crea la query per recuperare i dati in base al range di date
    query = """
    SELECT * FROM dati_arduino 
    WHERE data_ora BETWEEN %s AND %s
    """
    cur.execute(query, (start_date, end_date))  # Usa i segnaposto per prevenire SQL injection
    data = cur.fetchall()  # Ottieni i risultati

    cur.close()
    conn.close()

    # Trasforma i dati in formato JSON
    result = [{
        'temperatura': row[1],
        'umidita': row[2],
        'fumo': row[3],
        'data_ora': row[4],
    } for row in data]

    return jsonify(result)

@app.route('/logout')
def logout():
    session.pop('user_id', None)     # Rimuove user_id
    session.pop('username', None)    # Rimuove username
    return redirect(url_for('login'))  # Torna al login

if __name__ == "__main__":
    app.run(debug=True)