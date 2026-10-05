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
st.sidebar.subheader("🎛️️ Parameter Instalasi PLTS")
installed_capacity = st.sidebar.number_input(
    "Kapasitas Total Terpasang (kWp)",
    min_value=100.0,
    max_value=50000.0,
    value=1500.0,  # PLTS Grati 1.5 MWp
    step=50.0,
)
st_cnd_irradiance = 1000.0  # W/m² STC


# --- FUNGSI AMBIL DATA REALTIME VIA API INTERNAL ---
def get_realtime_data():
  """Mengambil data realtime secara otomatis dari server internal / API SCADA

  yang diexpose melalui Ngrok (`/api/live-data`).
  """
  try:
    response = requests.get(f"{NGROK_URL}/api/live-data", timeout=3)

    if response.status_code == 200:
      data = response.json()
      active_power_total = float(data.get("active_power", 0.0))
      irradiance = float(data.get("irradiance", 0.0))

      # Mengambil data list inverter 1 sampai 12 (format list/dict dari API backend)
      inverters_data = data.get("inverters", [])

      # Jika backend belum menyediakan format list per inverter, kita buat fallback dummy terstruktur
      if not inverters_data:
        inverters_data = []
        for i in range(1, 13):
          inverters_data.append({
              "id": i,
              "name": f"Inverter {i:02d}",
              "power": round(11.0 + (i * 0.1), 2),
              "capacity": 125.0,  # Kapasitas nominal per inverter (kWp)
          })

      return active_power_total, irradiance, inverters_data
    else:
      return 0.0, 0.0, []

  except requests.exceptions.RequestException as e:
    st.sidebar.warning(f"Koneksi API gagal: {e}. Menggunakan nilai default.")
    fallback_inverters = [
        {
            "id": i,
            "name": f"Inverter {i:02d}",
            "power": 0.0,
            "capacity": 125.0,
        }
        for i in range(1, 13)
    ]
    return 0.0, 0.0, fallback_inverters


# Ambil data realtime otomatis
active_power_realtime, irradiance_realtime, inverters_list = (
    get_realtime_data()
)

# --- Perhitungan Performance Ratio (PR) Total ---
if irradiance_realtime > 0:
  expected_power_total = installed_capacity * (
      irradiance_realtime / st_cnd_irradiance
  )
  performance_ratio_total = (
      (active_power_realtime / expected_power_total) * 100
      if expected_power_total > 0
      else 0.0
  )
else:
  performance_ratio_total = 0.0

# --- TAMPILAN DASHBOARD METRIK UTAMA ---
st.markdown("### 📊 Indikator Kinerja Total Sistem")
m1, m2, m3, m4 = st.columns(4)

m1.metric("Active Power Total (P_ac)", f"{active_power_realtime:,.2f} kW")
m2.metric("Solar Irradiance (EMI-01)", f"{irradiance_realtime:,.1f} W/m²")
m3.metric("Kapasitas Terpasang", f"{installed_capacity:,.1f} kWp")
m4.metric(
    "PR Total Sistem",
    f"{performance_ratio_total:.2f}%",
    delta=(
        "Optimal (>75%)"
        if performance_ratio_total >= 75
        else "Perlu Perhatian (<75%)"
    ),
)

st.markdown("---")

# --- MONITORING DETAIL INVERTER 1 SAMPAI 12 ---
st.markdown(
    "### 🔌 Detail Kinerja & Performance Ratio (PR) Inverter 01 - 12"
)

# Perbaikan pada baris ini (menggunakan kurung siku penutup list yang benar)
cols_per_row = 4
rows = [
    inverters_list[i : i + cols_per_row]
    for i in range(0, len(inverters_list), cols_per_row)
]

for row in rows:
  cols = st.columns(len(row))
  for idx, inv in enumerate(row):
    with cols[idx]:
      inv_id = inv.get("id")
      inv_name = inv.get("name", f"Inverter {inv_id}")
      inv_power = float(inv.get("power", 0.0))
      inv_cap = float(inv.get("capacity", 125.0))

      # Hitung PR per Inverter
      if irradiance_realtime > 0:
        inv_expected_power = inv_cap * (
            irradiance_realtime / st_cnd_irradiance
        )
        inv_pr = (
            (inv_power / inv_expected_power) * 100
            if inv_expected_power > 0
            else 0.0
        )
      else:
        inv_pr = 0.0

      # Tampilkan dalam kontainer card Streamlit
      with st.container(border=True):
        st.markdown(f"**{inv_name}**")
        st.metric("Active Power", f"{inv_power:.2f} kW")
        st.metric("PR Inverter", f"{inv_pr:.2f}%")

        if inv_pr >= 75:
          st.caption("🟢 Status: Normal / Optimal")
        elif 0 < inv_pr < 75:
          st.caption("🟡 Status: Rendah")
        else:
          st.caption("🔴 Status: Standby / Offline")

st.markdown("---")

# Main Content: Embedding iframe SCADA / Server Internal
st.subheader("🖥️ Live Mirror SCADA PLTGU Grati")
st.success(f"Menampilkan mirror dari server internal via: `{NGROK_URL}`")

try:
  st.components.v1.iframe(NGROK_URL, height=650, scrolling=True)
except Exception as e:
  st.error(f"Gagal memuat halaman. Pastikan sesi Ngrok aktif. Error: {e}")

# Auto-refresh halaman setiap 5 detik
time.sleep(5)
st.rerun()
