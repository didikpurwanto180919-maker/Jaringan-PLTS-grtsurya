import requests
import streamlit as st

# URL Ngrok sumber data/SCADA internal
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"


def get_realtime_data():
  """Mengambil data realtime secara otomatis dari server internal / API SCADA

  yang diexpose melalui Ngrok.
  """
  try:
    # Mengarahkan request ke endpoint API di PC kantor Anda
    # Contoh endpoint: https://reveler-striking-feminist.ngrok-free.dev/api/live-data
    response = requests.get(f"{NGROK_URL}/api/live-data", timeout=3)

    if response.status_code == 200:
      data = response.json()
      # Pastikan key JSON sesuai dengan yang dikirim oleh server kantor
      active_power = float(data.get("active_power", 0.0))
      irradiance = float(data.get("irradiance", 0.0))
      return active_power, irradiance
    else:
      # Jika server merespons tapi ada error (misal 404 atau 500)
      return 0.0, 0.0

  except requests.exceptions.RequestException as e:
    # Penanganan jika koneksi ke Ngrok terputus / offline
    st.sidebar.error(f"Koneksi API Gagal: {e}")
    return 0.0, 0.0
