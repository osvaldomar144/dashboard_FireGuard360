from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
#from djitellopy import Tello
import time
from datetime import datetime, timedelta
import random
import os 
from werkzeug.utils import secure_filename

app = Flask(__name__)



@app.context_processor
def inject_user():
    return dict(username=session.get('username'))

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

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT temperatura, umidita, fumo FROM dati_arduino ORDER BY data_ora DESC LIMIT 1')
    row = cur.fetchone()

    cur.close()
    conn.close()

    temperatura = row[0] if row else "N/A"
    umidita = row[1] if row else "N/A"
    fumo = row[2] if row else "N/A"

    return render_template(
        'index.html',
        username=session.get('username'),
        temperatura=temperatura,
        umidita=umidita,
        fumo=fumo
    )

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

@app.route('/get_last_events')
def get_last_events():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('SELECT data_ora, evento FROM eventi ORDER BY data_ora DESC')
    rows = cur.fetchall()

    cur.close()
    conn.close()

    eventi = [{"data_ora": row[0].strftime("%Y-%m-%d %H:%M:%S"), "evento": row[1]} for row in rows]
    return jsonify(eventi)

@app.route('/get_stats')
def get_stats():
    range_option = request.args.get('range', 'tutto')
    
    conn = get_db_connection()
    cur = conn.cursor()

    # Filtro per tabella dati_arduino
    if range_option == 'oggi':
        filtro_arduino = "WHERE DATE(data_ora) = CURDATE()"
        filtro_eventi = "AND DATE(data_ora) = CURDATE()"
    elif range_option == '7':
        filtro_arduino = "WHERE data_ora >= NOW() - INTERVAL 7 DAY"
        filtro_eventi = "AND data_ora >= NOW() - INTERVAL 7 DAY"
    elif range_option == '30':
        filtro_arduino = "WHERE data_ora >= NOW() - INTERVAL 30 DAY"
        filtro_eventi = "AND data_ora >= NOW() - INTERVAL 30 DAY"
    else:
        filtro_arduino = ""
        filtro_eventi = ""

    # Media dei valori dal sensore
    cur.execute(f"SELECT AVG(temperatura), AVG(umidita), AVG(fumo) FROM dati_arduino {filtro_arduino}")
    media = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({
        "media_temperatura": round(media[0], 1) if media[0] else 0,
        "media_umidita": round(media[1], 1) if media[1] else 0,
        "media_fumo": round(media[2], 1) if media[2] else 0,
       
    })

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

    # Query per ottenere gli ultimi 10 record (per grafico)
    cur.execute('SELECT id, temperatura, umidita, fumo, data_ora FROM dati_arduino ORDER BY data_ora DESC LIMIT 10')
    rows2 = cur.fetchall()

    # Query per ottenere tutti i record (per la tabella)
    cur.execute('SELECT id, temperatura, umidita, fumo, data_ora FROM dati_arduino ORDER BY data_ora DESC')
    rows = cur.fetchall()

    dati = []
    labels = []
    full_dates = []
    temperatura = []
    fumo = []
    umidita = []

    # Popola i dati per la tabella
    for row in rows[::-1]:  # Inverti per mostrare i dati in ordine cronologico
        dati.append({
            'id': row[0],
            'temperatura': row[1],
            'umidita': row[2],
            'fumo': row[3],
            'data_ora': row[4].strftime("%Y-%m-%d %H:%M:%S")
        })

    # Popola i dati per i grafici (ultimi 10)
    for row2 in rows2[::-1]:  # Inverti per grafici in ordine cronologico
        full_date = row2[4].strftime("%Y-%m-%d %H:%M")  # Data completa (esempio: 2025-03-31 14:05)
        labels.append(row2[4].strftime("%H:%M"))  # Per l'asse X, mostra solo ora e minuti
        full_dates.append(full_date)  #
        temperatura.append(row2[1])
        umidita.append(row2[2])  # 👈 aggiunto
        fumo.append(row2[3])

    cur.close()
    conn.close()

    return render_template(
        'dati_arduino.html',
        dati=dati,
        chart_labels=labels,
        chart_temperatura=temperatura,
        chart_fumo=fumo,
        chart_umidita=umidita,
        full_dates=full_dates
    )

@app.route('/controlli')
def controlli():
    # Percorso del modello .obj
    model_filename = 'Modern cottage_01_OBJ.obj'  # Assicurati che il nome del file sia corretto
    model_path = url_for('static', filename=f'models/{model_filename}')
    
    # Passa il percorso del modello al template
    return render_template('controlli.html', model_path=model_path)

@app.route('/controllo/rele/<stato>', methods=['POST'])
def controllo_rele(stato):
    # Logica reale qui
    if stato == 'on':
        # Attiva relè fisicamente
        stato_attuale = 'on'
    elif stato == 'off':
        # Disattiva relè fisicamente
        stato_attuale = 'off'
    elif stato == 'stato':
        # Recupera stato attuale reale o simulato
        stato_attuale = 'off'  # oppure valore da variabile/DB
    else:
        stato_attuale = 'errore'

    return jsonify({"stato": stato_attuale})

from datetime import datetime, timedelta

@app.route('/get_last_risk_event')
def get_last_risk_event():
    conn = get_db_connection()
    cur = conn.cursor()

    # Ottieni l'ultimo evento di rischio
    cur.execute('SELECT evento, data_ora FROM eventi WHERE evento LIKE "Pericolo%" OR evento LIKE "Attenzione%" ORDER BY data_ora DESC LIMIT 1')
    row = cur.fetchone()
    
    cur.close()
    conn.close()

    if row:
        # Recupera la data dell'evento
        event_date = row[1]

        # Verifica se event_date è già un oggetto datetime
        if isinstance(event_date, datetime):
            event_time = event_date
        else:
            # Se per qualche motivo event_date non è già un datetime, usiamo strptime
            event_time = datetime.strptime(event_date, "%Y-%m-%d %H:%M:%S")

        # Confronta la data dell'evento con il momento attuale
        now = datetime.now()
        time_diff = now - event_time

        # Se l'evento è nelle ultime 24 ore, invia l'evento, altrimenti invia un valore None
        if time_diff <= timedelta(days=1):
            # Formatta la data dell'evento come stringa per la risposta JSON
            event_date_str = event_time.strftime("%Y-%m-%d %H:%M:%S")
            return jsonify({
                'rischio': row[0],
                'data_ora': event_date_str  # Rispondi con la data formattata come stringa
            })
        else:
            return jsonify({'rischio': None, 'data_ora': None})
    else:
        return jsonify({'rischio': None, 'data_ora': None})
@app.route('/allarmi')
def allarmi():
    return render_template('allarmi.html', username=session.get('username'))

@app.route('/get_allarmi_storico')
def get_allarmi_storico():
    data_da = request.args.get('da')
    data_a = request.args.get('a')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT data_ora, evento 
        FROM eventi 
        WHERE (evento LIKE '%attenzione%' OR evento LIKE '%pericolo%')
    """
    params = []

    if data_da and data_a:
        query += " AND DATE(data_ora) BETWEEN %s AND %s"
        params.extend([data_da, data_a])

    query += " ORDER BY data_ora DESC"

    cur.execute(query, params)
    risultati = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(risultati)

def get_mock_battery_level():
    return random.randint(0, 100)

@app.route('/drone')
def drone_page():
    return render_template('drone_page.html', battery=get_mock_battery_level())

@app.route('/drone/status')
def drone_status():
    return jsonify({"battery": get_mock_battery_level(), "status": "connected"})


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

@app.route('/profilo', methods=['GET', 'POST'])
def profilo():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nuovo_username = request.form['username']
        nuova_password = request.form['password']
        avatar = request.files.get('avatar')

        # Gestisci la password
        if nuova_password:
            # Usa un hash per la password (es. werkzeug.security)
            hashed_password = generate_password_hash(nuova_password)  # Usa questa funzione se stai usando werkzeug
            cur.execute('UPDATE utenti SET username = %s, password_hash = %s WHERE id = %s',
                        (nuovo_username, hashed_password, user_id))
        else:
            cur.execute('UPDATE utenti SET username = %s WHERE id = %s', (nuovo_username, user_id))

        # Gestisci l'avatar
        if avatar:
            # Salva l'avatar nella cartella uploads
            avatar_filename = f"{nuovo_username}.jpg"
            avatar.save(f"static/uploads/{avatar_filename}")
        
        # Aggiorna la sessione con il nuovo nome utente
        session['username'] = nuovo_username

        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('profilo'))  # Ritorna alla stessa pagina per aggiornare i dati

    # GET
    cur.execute('SELECT username FROM utenti WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('profilo.html', username=user[0])

@app.route('/aggiorna_profilo', methods=['POST'])
def aggiorna_profilo():
    nuovo_username = request.form['username']
    file = request.files.get('avatar')

    # aggiorna il nome utente nel DB (implementa tu)
    # salva immagine profilo se presente
    if file:
        file.save(f"static/uploads/{nuovo_username}.jpg")

    session['username'] = nuovo_username
    return redirect(url_for('profilo'))



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.context_processor
def inject_username():
    return dict(username=session.get('username'))

if __name__ == "__main__":
    app.run(debug=True)