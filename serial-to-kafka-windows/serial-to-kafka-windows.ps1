# PowerShell script per avviare lo script serial_to_kafka su Windows

$envDir = ".venv-serial-kafka"
$script = "serial-to-kafka-windows.py"

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
