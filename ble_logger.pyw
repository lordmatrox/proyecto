import asyncio
import os
import subprocess
from datetime import datetime, timedelta
from bleak import BleakClient

# === Configuración BLE ===
TARGET_BLE_ADDRESS = "26:7C:79:33:0F:DA"
CHARACTERISTIC_UUID = "2a56"
DATA_DIR = "datos"
os.makedirs(DATA_DIR, exist_ok=True)

# === Estado ===
current_hour = None
soil_file = None
amb_file = None
temp_file = None
last_git_push = datetime.now()

# === Generar nombres por hora ===
def get_filenames():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H")
    soil = os.path.join(DATA_DIR, f"humedad_suelo_{timestamp}.csv")
    amb = os.path.join(DATA_DIR, f"humedad_ambiente_{timestamp}.csv")
    temp = os.path.join(DATA_DIR, f"temperatura_{timestamp}.csv")
    return soil, amb, temp

# === Inicializar CSV ===
def init_csv(file_path, header):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(header + "\n")

# === Subir a GitHub ===
def push_to_github():
    try:
        subprocess.run(["git", "add", DATA_DIR], check=True)
        subprocess.run(["git", "commit", "-m", "📦 Datos actualizados automáticamente"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 Datos subidos a GitHub.")
    except subprocess.CalledProcessError as e:
        print("❌ Error al subir a GitHub:", e)

# === Manejar datos BLE ===
def handle_data(_, data):
    global current_hour, soil_file, amb_file, temp_file, last_git_push

    try:
        decoded = data.decode("utf-8").strip()
        suelo, ambiente, temperatura = decoded.split(",")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hour_now = datetime.now().strftime("%Y-%m-%d_%H")

        if hour_now != current_hour:
            current_hour = hour_now
            soil_file, amb_file, temp_file = get_filenames()
            init_csv(soil_file, "timestamp,humedad_suelo")
            init_csv(amb_file, "timestamp,humedad_ambiente")
            init_csv(temp_file, "timestamp,temperatura")

        with open(soil_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp},{suelo}\n")
        with open(amb_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp},{ambiente}\n")
        with open(temp_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp},{temperatura}\n")

        print(f"[{timestamp}] Suelo: {suelo}% | Ambiente: {ambiente}% | Temp: {temperatura}°C")

        if datetime.now() - last_git_push >= timedelta(minutes=30):
            push_to_github()
            last_git_push = datetime.now()

    except Exception as e:
        print("❌ Error procesando datos:", e)

# === Bucle infinito con reconexión ===
async def start_listener():
    while True:
        try:
            print(f"🔍 Intentando conexión BLE con {TARGET_BLE_ADDRESS}...")
            async with BleakClient(TARGET_BLE_ADDRESS) as client:
                print("✅ Conexión BLE establecida.")
                await client.start_notify(CHARACTERISTIC_UUID, handle_data)
                print("📡 Escuchando datos... Ctrl+C para salir.")
                while True:
                    await asyncio.sleep(1)
        except Exception as e:
            print(f"⚠️  BLE desconectado o error: {e}")
            print("🔁 Reintentando en 10 segundos...")
            await asyncio.sleep(10)

# === Ejecutar ===
if __name__ == "__main__":
    try:
        with open("log_inicio.txt", "a", encoding="utf-8") as f:
            f.write(f"Inicio: {datetime.now()}\n")
        asyncio.run(start_listener())
    except KeyboardInterrupt:
        print("🛑 Finalizado por el usuario.")
