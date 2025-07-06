# === VARIABILI DI AMBIENTE ===
$env:USE_SIMULATION = "true"               # o "true" se vuoi usare il video
$env:SIMULATION_SOURCE = "fire.mp4"         # il video di simulazione (se USE_SIMULATION=true)
$env:YOLO_MODEL_PATH = "best.pt"            # il tuo modello YOLO
$env:FRAME_WIDTH = "640"
$env:FRAME_HEIGHT = "480"

# PowerShell script per avviare lo script serial_to_kafka su Windows

$envDir = ".venv-drone-stream"
$script = "drone_stream_server.py"

# Controlla se Python è installato
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python non è installato o non è presente nel PATH."
    exit 1
}

# Crea ambiente virtuale se non esiste
if (-Not (Test-Path $envDir)) {
    Write-Host "Creo ambiente virtuale Python..."
    python -m venv $envDir
}

# Attiva l'ambiente virtuale
& "$envDir\Scripts\Activate.ps1"

# Installa le dipendenze (solo se mancano)
pip install --upgrade pip
pip install -r requirements.txt

# Avvia lo script
Write-Host "Avvio script..."
python $script
