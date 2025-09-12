import os
import glob
import random
from pathlib import Path
import pandas as pd
import numpy as np

# ========= Config =========
IN_PATH  = os.environ.get("PRSA_IN",  "./in")                 # cartella o file
OUT_CSV  = os.environ.get("PRSA_OUT_CSV",  "./out/fg360_prsa_replay.csv")
MAX_ROWS = int(os.environ.get("PRSA_MAX_ROWS", "0"))                   # 0 = nessun limite

# Base per lat/lon sintetici (Beijing) e griglia ~1km
BJ_LAT, BJ_LON = 39.9042, 116.4074
GRID_DEG = 0.01
MIN_LAT, MIN_LON = 39.4, 115.8

def ensure_paths():
    Path(Path(OUT_CSV).parent).mkdir(parents=True, exist_ok=True)

def list_input_files(in_path: str):
    p = Path(in_path)
    if p.is_dir():
        files = sorted(glob.glob(str(p / "*.csv")))
    else:
        files = [str(p)]
    if not files:
        raise FileNotFoundError(f"Nessun CSV trovato in {in_path}")
    return files

def ts_from_cols(df: pd.DataFrame) -> pd.Series:
    if not {"year","month","day","hour"}.issubset(df.columns):
        raise ValueError("Il CSV PRSA deve contenere: year, month, day, hour")
    ts_local = pd.to_datetime(
        dict(year=df["year"], month=df["month"], day=df["day"], hour=df["hour"]),
        errors="coerce"
    )
    # Beijing -> Asia/Shanghai -> converti in UTC
    ts_local = ts_local.dt.tz_localize("Asia/Shanghai", nonexistent="NaT", ambiguous="NaT")
    ts_utc = ts_local.dt.tz_convert("UTC")
    return ts_utc

def rel_humidity_from_temp_dewp(temp_c: pd.Series, dewp_c: pd.Series) -> pd.Series:
    a, b = 17.625, 243.04
    with np.errstate(invalid="ignore"):
        gamma_d = (a * dewp_c) / (b + dewp_c)
        gamma_t = (a * temp_c) / (b + temp_c)
        rh = 100.0 * np.exp(gamma_d - gamma_t)
    return pd.Series(np.clip(rh, 0.0, 100.0))

def gas_index(so2, no2, co):
    # CO è in mg/m^3. Lo porto a μg/m^3 per avere ordini di grandezza simili
    co_scaled = co * 1000.0
    return 2.0 * so2 + 1.5 * no2 + 1.0 * co_scaled

def stable_station_coords(station: str):
    rnd = random.Random(station)
    dlat = rnd.uniform(-0.35, 0.35)
    dlon = rnd.uniform(-0.45, 0.45)
    return BJ_LAT + dlat, BJ_LON + dlon

def to_cell_id(lat: float, lon: float) -> str:
    r = int((lat - MIN_LAT) / GRID_DEG)
    c = int((lon - MIN_LON) / GRID_DEG)
    return f"CELL_{r}_{c}"

def sanitize_station(station: str) -> str:
    if pd.isna(station):
        return "PRSA-UNK"
    s = str(station).strip().upper().replace(" ", "").replace("-", "")
    return f"PRSA-{s[:16]}"

def process_one(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)

    # Timestamp UTC
    df["ts"] = ts_from_cols(df)

    # Colonne richieste: se mancano, riempi
    for col in ["TEMP","DEWP","WSPM","PM2.5","SO2","NO2","CO","station"]:
        if col not in df.columns:
            df[col] = np.nan

    # Feature derivate
    df["hum"] = rel_humidity_from_temp_dewp(df["TEMP"], df["DEWP"])
    df["gas"] = gas_index(df["SO2"].fillna(0), df["NO2"].fillna(0), df["CO"].fillna(0))

    # Coordinate/sensori stabili per stazione
    sensors = df["station"].fillna("UNK").astype(str)
    lat_list, lon_list = [], []
    for st in sensors:
        la, lo = stable_station_coords(st)
        lat_list.append(la); lon_list.append(lo)
    df["lat"] = lat_list; df["lon"] = lon_list
    df["cell_id"] = [to_cell_id(la, lo) for la, lo in zip(df["lat"], df["lon"])]

    df["sensor_id"] = [sanitize_station(st) for st in sensors]
    rnd = random.Random(42)
    df["battery"] = [rnd.randint(60, 100) for _ in range(len(df))]

    out = pd.DataFrame({
        "ts": df["ts"],
        "sensor_id": df["sensor_id"],
        "lat": df["lat"].astype(float),
        "lon": df["lon"].astype(float),
        "cell_id": df["cell_id"],
        "temp": df["TEMP"].astype(float),
        "hum": df["hum"].astype(float),
        "gas": df["gas"].astype(float),
        "pm25": df["PM2.5"].astype(float),
        "wind": df["WSPM"].astype(float),
        "battery": df["battery"].astype(int),
    })
    # Keep righe con timestamp e misure principali valide
    out = out.dropna(subset=["ts","temp","pm25","wind"])
    return out

def main():
    ensure_paths()
    files = list_input_files(IN_PATH)

    parts = []
    for fp in files:
        print(f"[PRSA] Leggo {fp}")
        try:
            parts.append(process_one(fp))
        except Exception as e:
            print(f"  -> salto {fp}: {e}")

    if not parts:
        raise RuntimeError("Nessun file valido elaborato.")

    df = pd.concat(parts, ignore_index=True).sort_values("ts").reset_index(drop=True)
    if MAX_ROWS > 0:
        df = df.iloc[:MAX_ROWS].copy()

    # --- CSV per il replayer ---
    print(f"[PRSA] Scrivo CSV: {OUT_CSV}")
    df_csv = df.copy()
    df_csv["time"] = df_csv["ts"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # stringa ISO UTC
    df_csv = df_csv[["time","lat","lon","cell_id","sensor_id","temp","hum","gas","pm25","wind","battery"]]
    Path(OUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    df_csv.to_csv(OUT_CSV, index=False)

    print(f"[PRSA] Done. Righe: {len(df_csv)}")
    print(f"       CSV -> {OUT_CSV}")

if __name__ == "__main__":
    main()
