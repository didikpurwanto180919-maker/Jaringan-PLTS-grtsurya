from datetime import datetime
import time
import requests
import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

# Judul Aplikasi & Tanggal Realtime
st.title("⚡ Live Dashboard Monitoring & Performance Ratio (PR) GRT Surya")

# Menampilkan Tanggal dan Waktu Realtime
current_time_str = datetime.now().strftime("%A, %d %B %Y - %H:%M:%S")
st.markdown(f"📅 **Waktu Server Realtime:** `{current_time_str}`")
st.markdown("---")

# URL Ngrok sumber data/SCADA internal
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"

# Koordinat Global Solar Atlas PLTS Grati
LATITUDE = -7.678604
LONGITUDE = 112.905121

# Sidebar Konfigurasi Sistem
st.sidebar.header("⚙️ Status & Konfigurasi")
st.sidebar.markdown(f"**URL Ngrok:** `{NGROK_URL}`")
st.sidebar.markdown(f"**Lokasi GSA:** `{LATITUDE}, {LONGITUDE}`")
st.sidebar.markdown("⏱️ **Auto-Refresh:** Setiap 60 Detik")

st.sidebar.markdown("---")
st.sidebar.subheader("🎛 Parameter Instalasi PLTS")
installed_capacity = st.sidebar.number_input(
    "Kapasitas Total Terpasang (kWp)",
    min_value=100.0,
    max_value=50000.0,
    value=1500.0,  # PLTS Grati 1.5 MWp
    step=50.0,
)
st_cnd_irradiance = 1000.0  # W/m² STC


# --- FUNGSI AMBIL DATA ACTIVE POWER & IRRADIANCE ---
def get_realtime_data():
  active_power_total = 0.0
  inverters_data = []

  # 1. Ambil Active Power & Inverter dari API Server Internal Kantor via Ngrok
  try:
    response = requests.get(f"{NGROK_URL}/api/live-data", timeout=3)
    if response.status_code == 200:
      data = response.json()
      active_power_total = float(data.get("active_power", 0.0))
      inverters_data = data.get("inverters", [])
      st.sidebar.success("Status: Terhubung ke SCADA Lokal")
  except Exception as e:
    st.sidebar.warning(f"API Lokal Offline. Menggunakan nilai default.")

  # Jika data inverter dari API lokal kosong, buat struktur default 1-12
  if not inverters_data:
    for i in range(1, 13):
      inverters_data.append({
          "id": i,
          "name": f"Inverter {i:02d}",
          "power": 0.0,
          "capacity": 125.0,
      })

  # 2. Irradiance berdasarkan titik referensi Global Solar Atlas Grati
  irradiance = 825.5  # Nilai acuan radiasi surya wilayah Grati (W/m²)

  return active_power_total, irradiance, inverters_data


# Ambil data realtime
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
m2.metric(
    "Irradiance (Global Solar Atlas)", f"{irradiance_realtime:,.1f} W/m²"
)
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

cols_per_row = 4
rows = [
    inverters_list[i : i + cols_per_row]
    for i in range(0, len(inverters_list), cols_per_row)
]

for row in rows:
  cols = st.columns(len(row))
  for idx, inv in enumerate(row):
    with cols[idx]:
      inv_name = inv.get("name", f"Inverter {idx+1:02d}")
      inv_power = float(inv.get("power", 0.0))
      inv_cap = float(inv.get("capacity", 125.0))

      # Hitung PR per Inverter berdasarkan Irradiance
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

      with st.container(border=True):
        st.markdown(f"**{inv_name}**")
        st.metric("Active Power", f"{inv_power:.2f} kW")
        st.metric("PR Inverter", f"{inv_pr:.2f}%")

        if inv_pr >= 75:
          st.caption("🟢 Status: Normal / Optimal")
        elif 0 < inv_pr < 75:
          st.caption("🟡 Status: Rendah")
        else:
          st.caption("🔴 Status: Offline")

st.markdown("---")

# Main Content: Embedding iframe SCADA / Server Internal
st.subheader("🖥️ Live Mirror SCADA PLTGU Grati")
st.success(f"Menampilkan mirror dari server internal via: `{NGROK_URL}`")

try:
  st.components.v1.iframe(NGROK_URL, height=650, scrolling=True)
except Exception as e:
  st.error(f"Gagal memuat halaman iframe. Error: {e}")

# Auto-refresh halaman setiap 60 detik
time.sleep(60)
st.rerun()
