from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
#from djitellopy import Tello
import time
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Cambia con una chiave segreta sicura
#drone = Tello()

# Variabile per tenere traccia della connessione al drone
#drone_connected = False

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

    return render_template('index.html', username=session.get('username'))

@app.route('/get_data')
def get_data():
    # Connessione al database per recuperare tutti i dati Arduino
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT * FROM dati_arduino ORDER BY data_ora DESC;')
    dati = cur.fetchall()

    cur.close()
    conn.close()

    data = [{
        "temperatura": row[1],
        "umidita": row[2],
        "fumo": row[3],
        "data_ora": row[4].strftime("%Y-%m-%d %H:%M:%S")
    } for row in dati]

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


@app.route('/dati-arduino')
def dati_arduino():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT id, temperatura, umidita, fumo, data_ora FROM dati_arduino ORDER BY data_ora DESC LIMIT 50')
    rows = cur.fetchall()

    dati = []
    labels = []
    temperatura = []
    fumo = []
    umidita = []  # 👈 aggiunto

    for row in rows[::-1]:  # inverti per grafici in ordine cronologico
        dati.append({
            'id': row[0],
            'temperatura': row[1],
            'umidita': row[2],
            'fumo': row[3],
            'data_ora': row[4].strftime("%Y-%m-%d %H:%M:%S")
        })
        labels.append(row[4].strftime("%H:%M"))
        temperatura.append(row[1])
        umidita.append(row[2])  # 👈 aggiunto
        fumo.append(row[3])

    cur.close()
    conn.close()

    return render_template(
        'dati_arduino.html',
        dati=dati,
        chart_labels=labels,
        chart_temperatura=temperatura,
        chart_fumo=fumo,
        chart_umidita=umidita  # 👈 aggiunto
    )


def get_mock_battery_level():
    return random.randint(0, 100)

@app.route('/drone')
def drone_page():
    return render_template('drone_page.html', battery=get_mock_battery_level())

@app.route('/drone/status')
def drone_status():
    return jsonify({"battery": get_mock_battery_level(), "status": "not connected"})


""" @app.route('/drone')
def drone_page():
    global drone_connected
    try:
        # Tenta la connessione al drone
        drone.connect()
        drone_connected = True
    except Exception as e:
        drone_connected = False
        print(f"Errore di connessione: {e}")

    # Ottieni livello batteria
    battery_level = drone.get_battery() if drone_connected else 0

    return render_template('drone_page.html', connected=drone_connected, battery=battery_level)

@app.route('/drone/status')
def drone_status():
    if drone_connected:
        battery_level = drone.get_battery()
        return jsonify({"battery": battery_level, "status": "connected"})
    else:
        return jsonify({"battery": 0, "status": "not connected"})

@app.route('/drone/takeoff', methods=['POST'])
def drone_takeoff():
    if drone_connected:
        drone.takeoff()
        return jsonify({"status": "taken off"})
    else:
        return jsonify({"status": "not connected"})

@app.route('/drone/land', methods=['POST'])
def drone_land():
    if drone_connected:
        drone.land()
        return jsonify({"status": "landed"})
    else:
        return jsonify({"status": "not connected"}) """

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)