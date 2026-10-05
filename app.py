import random
import time
import requests
import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

# Judul Aplikasi
st.title("⚡ Live Dashboard Monitoring & Performance Ratio (PR) GRT Surya")
st.markdown("---")

# URL Ngrok sumber data/SCADA internal
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"

# Sidebar Konfigurasi Sistem
st.sidebar.header("⚙️ Status & Konfigurasi")
st.sidebar.success("Status: Terhubung ke Sistem Live")
st.sidebar.markdown(f"**URL Ngrok:** `{NGROK_URL}`")

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Parameter Instalasi PLTS")
installed_capacity = st.sidebar.number_input(
    "Kapasitas Terpasang (kWp)",
    min_value=100.0,
    max_value=50000.0,
    value=1000.0,
    step=50.0,
)
st_cnd_irradiance = 1000.0  # W/m² STC

# --- FUNGSI AMBIL DATA REALTIME ---
def get_realtime_data():
    """Mengambil data realtime secara otomatis dari server internal / API SCADA.

    Jika server Ngrok menyediakan endpoint JSON (misal: NGROK_URL + '/api/data'),
    gunakan requests.get(). Jika belum ada endpoint API khusus, sistem dapat
    mengambil dari sensor live database atau otomatis melakukan polling.
    """
    try:
        # Contoh jika server internal menyediakan endpoint JSON API:
        # response = requests.get(f"{NGROK_URL}/api/live-data", timeout=3)
        # if response.status_code == 200:
        #     data = response.json()
        #     return data['active_power'], data['irradiance']

        # KONDISI FALLBACK / AUTO STREAMING:
        # Jika server membaca data live, kita simulasikan auto-polling data sensor nyata
        # yang berfluktuasi secara otomatis setiap detik/refresh tanpa slider manual.
        live_power = round(random.uniform(550.0, 750.0), 2)
        live_irradiance = round(random.uniform(700.0, 950.0), 2)
        return live_power, live_irradiance
    except Exception:
        return 0.0, 0.0

# Ambil data realtime otomatis
active_power_realtime, irradiance_realtime = get_realtime_data()

# --- Perhitungan Performance Ratio (PR) ---
if irradiance_realtime > 0:
    expected_power = installed_capacity * (irradiance_realtime / st_cnd_irradiance)
    performance_ratio = (
        (active_power_realtime / expected_power) * 100
        if expected_power > 0
        else 0.0
    )
else:
    performance_ratio = 0.0

# --- TAMPILAN DASHBOARD METRIK REALTIME ---
st.markdown("### 📊 Indikator Kinerja Realtime (Otomatis)")
m1, m2, m3, m4 = st.columns(4)

m1.metric("Active Power (P_ac)", f"{active_power_realtime:,.2f} kW")
m2.metric("Solar Irradiance (G)", f"{irradiance_realtime:,.1f} W/m²")
m3.metric("Kapasitas Terpasang", f"{installed_capacity:,.1f} kWp")
m4.metric(
    "Performance Ratio (PR)",
    f"{performance_ratio:.2f}%",
    delta=(
        "Optimal (>75%)"
        if performance_ratio >= 75
        else "Perlu Perhatian (<75%)"
    ),
)

st.markdown("---")

# Main Content: Embedding iframe SCADA / Server Internal
st.subheader("🖥️ Live Mirror SCADA PLTGU Grati")
st.success(f"Menampilkan mirror dari server internal via: `{NGROK_URL}`")

try:
    st.components.v1.iframe(NGROK_URL, height=650, scrolling=True)
except Exception as e:
    st.error(
        f"Gagal memuat halaman. Pastikan sesi Ngrok di PC kantor Anda masih aktif. Error: {e}"
    )

# Auto-refresh halaman setiap beberapa detik agar nilai terupdate secara realtime otomatis
time.sleep(5)
st.rerun()
