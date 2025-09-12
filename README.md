# FireGuard360 – Big Data Streaming & Analytics

FireGuard360 è una piattaforma di monitoraggio in tempo reale che integra **Kafka**, **Spark**, **Cassandra** e **MinIO** per la raccolta, l’elaborazione e la visualizzazione dei dati provenienti da sensori ambientali.  
La dashboard di controllo è sviluppata in **Flask**.

---

## Requisiti

- Docker >= 20.x
- Docker Compose >= 2.x
- Almeno **8 GB di RAM** disponibili per i container
- Connessione internet per scaricare le immagini

---

## Servizi inclusi

- **Zookeeper** – coordinatore per Kafka  
- **Kafka** – broker di messaggi (topic `sensors.raw`, `sensors.replay`, `risk.index`)  
- **Kafka UI** – interfaccia grafica web per esplorare i topic  
- **MinIO** – data lake S3-compatibile per dati grezzi e gold  
- **Cassandra** – database NoSQL per metriche e indici di rischio  
- **Spark Master & Workers** – cluster per job di streaming e batch  
- **Spark Jobs**:
  - `spark-agg1m-live` – aggregazioni 1m da `sensors.raw`
  - `spark-agg1m-replay` – aggregazioni 1m da `sensors.replay`
  - `spark-risk-index` – calcolo indici di rischio su finestre 10m
  - `spark-batch-daily` – job batch rolling per dati giornalieri
- **Producers**:
  - `producer-synthetic` – genera eventi simulati
  - `producer-replayer` – riproduce dataset registrati
- **Flask Dashboard** – dashboard per visualizzazione dei dati e controlli

---

## ▶️ Avvio rapido

1. **Clona la repository** (se non già fatto)

   ```bash
   git clone <repo-url>
   cd <repo-folder>
   ```

2. **Avvia i container**
    ```
    docker compose up -d
    ```

3. **Verifica lo stato**
    ```
    docker ps
    ```

Tutti i servizi principali devono risultare Up o Healthy.