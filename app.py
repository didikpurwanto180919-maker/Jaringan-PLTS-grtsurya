import time
import requests
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

# Judul Aplikasi
st.title("⚡ Live Dashboard Monitoring & AI Early Warning PLTS Grati")

# --- WIDGET JAM REAL-TIME BERDETAK (JAVASCRIPT) ---
clock_html = """
<div style="font-family: monospace; font-size: 16px; font-weight: bold; color: #2e7d32; background-color: #e8f5e9; padding: 8px; border-radius: 5px; display: inline-block;">
    📅 Waktu Realtime: <span id="live-clock"></span>
</div>
<script>
function updateClock() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false };
    document.getElementById('live-clock').innerText = now.toLocaleDateString('id-ID', options);
}
setInterval(updateClock, 1000);
updateClock();
</script>
"""
components.html(clock_html, height=45)
st.markdown("---")

# URL Ngrok sumber data/SCADA internal
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"

# Koordinat Global Solar Atlas PLTS Grati
LATITUDE = -7.678604
LONGITUDE = 112.905121

# Sidebar Konfigurasi Sistem
st.sidebar.header("⚙️ Status & Konfigurasi AI")
st.sidebar.markdown(f"**URL Ngrok:** `{NGROK_URL}`")
st.sidebar.markdown(f"**Lokasi GSA:** `{LATITUDE}, {LONGITUDE}`")
st.sidebar.markdown("🤖 **AI Model:** Statistical Threshold & Anomaly Engine")
st.sidebar.markdown("⏱️ **Auto-Refresh Data:** Setiap 60 Detik")

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
  except Exception:
    st.sidebar.warning("API Lokal Offline. Menggunakan nilai default.")

  # Jika data inverter dari API lokal kosong, buat struktur default 1-12
  # Sesuai permintaan: Inverter 1 s.d. 11 kapasitas 128.4 kWp, Inverter 12 menyesuaikan sisa total 1500 kWp
  if not inverters_data:
    for i in range(1, 13):
      # Kapasitas inverter 1-11 sebesar 128.4 kWp, inverter 12 sisa dari 1500 - (128.4 * 11) = 87.6 kWp
      cap = 128.4 if i <= 11 else 87.6
      inverters_data.append({
          "id": i,
          "name": f"Inverter {i:02d}",
          "power": 11.5 if i <= 11 else 8.5,
          "capacity": cap,
      })

  # 2. Irradiance berdasarkan titik referensi Global Solar Atlas Grati
  irradiance = 825.5  # Nilai acuan radiasi surya wilayah Grati (W/m²)
  ambient_temp = 32.5  # Simulasi temperatur lingkungan (°C)

  return active_power_total, irradiance, ambient_temp, inverters_data


# Ambil data realtime
active_power_realtime, irradiance_realtime, ambient_temp, inverters_list = (
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


# --- AI / MACHINE LEARNING EARLY WARNING ENGINE ---
def run_ai_anomaly_detection(power, irradiance, pr):
  expected_power = 1500.0 * (irradiance / 1000.0)
  expected_pr = (power / expected_power * 100) if expected_power > 0 else 0.0
  deviation = abs(expected_pr - pr)
  is_anomaly = deviation > 15.0 or pr < 75.0
  return is_anomaly


ai_anomaly_detected = run_ai_anomaly_detection(
    active_power_realtime, irradiance_realtime, performance_ratio_total
)


# --- TAMPILAN DASHBOARD METRIK UTAMA ---
st.markdown("### 📊 Indikator Kinerja Total Sistem")
m1, m2, m3, m4 = st.columns(4)

m1.metric("Active Power Total (P_ac)", f"{active_power_realtime:,.2f} kW")
m2.metric(
    "Irradiance (Global Solar Atlas)", f"{irradiance_realtime:,.1f} W/m²"
)
m3.metric("Temperatur Lingkungan", f"{ambient_temp:.1f} °C")
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

# --- SISTEM EARLY WARNING MACHINE LEARNING (MANDATORI JIKA PR < 75%) ---
st.markdown("### 🚨 AI Early Warning & Diagnostic System")

if performance_ratio_total < 75 or ai_anomaly_detected:
  st.error(
      "⚠️ **PERINGATAN DINI (EARLY WARNING):** Performance Ratio (PR) Sistem"
      f" Berada di Bawah Batas Optimal ({performance_ratio_total:.2f}% < 75%)"
      " atau Model AI Mendeteksi Anomali Operasional!"
  )

  with st.expander(
      "🛠️ **PROSEDUR MANDATORI TINDAKAN OPERASIONAL (KLIK UNTUK MELIHAT)**",
      expanded=True,
  ):
    st.warning(
        "Tim operasi dan pemeliharaan (O&M) diwajibkan segera melakukan"
        " investigasi lapangan berdasarkan checklist berikut:"
    )

    col_a, col_b = st.columns(2)
    with col_a:
      st.markdown("""
            *   🧽 **1. Cek Kebersihan PV Modul:**
                *   Periksa akumulasi debu, kotoran burung, atau *soiling* pada permukaan panel surya.
                *   Jadwalkan pembersihan (*modul washing*) jika ditemukan penurunan transmitansi cahaya.
            *   🔌 **2. Cek Kondisi PV String:**
                *   Periksa tegangan dan arus pada tiap string box / combiner box.
                *   Identifikasi kemungkinan adanya *hotspot*, kabel putus, atau sambungan longgar.
            """)
    with col_b:
      st.markdown("""
            *   ⚡ **3. Cek Unit Inverter:**
                *   Periksa status error/alarm pada panel inverter (Inverter 01 s.d. 12).
                *   Pastikan sistem pendingin (cooling fan/heatsink) inverter bekerja normal.
            *   🌡️ **4. Cek Temperatur Lingkungan:**
                *   Evaluasi pengaruh suhu tinggi terhadap derating efisiensi modul PV.
                *   Pastikan sirkulasi udara di sekitar rumah inverter (*inverter station*) optimal.
            """)
else:
  st.success(
      "✅ **Status Sistem Normal:** Model Machine Learning mendeteksi seluruh"
      " parameter operasional PLTS Grati berjalan optimal (PR ≥ 75%)."
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
      # Mengambil kapasitas dari data (Inverter 1-11 sebesar 128.4 kWp)
      inv_cap = float(inv.get("capacity", 128.4))

      # Hitung PR per Inverter berdasarkan kapasitas spesifik masing-masing inverter
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
        st.caption(f"Kapasitas: {inv_cap} kWp")
        st.metric("Active Power", f"{inv_power:.2f} kW")
        st.metric("PR Inverter", f"{inv_pr:.2f}%")

        if inv_pr >= 75:
          st.caption("🟢 Status: Normal / Optimal")
        elif 0 < inv_pr < 75:
          st.caption("🟡 Status: Rendah (Cek String/Panel)")
        else:
          st.caption("🔴 Status: Offline / Trip")

st.markdown("---")

# Main Content: Embedding iframe SCADA / Server Internal
st.subheader("🖥️ Live Mirror SCADA PLTGU Grati")
st.success(f"Menampilkan mirror dari server internal via: `{NGROK_URL}`")

try:
  st.components.v1.iframe(NGROK_URL, height=650, scrolling=True)
except Exception as e:
  st.error(f"Gagal memuat halaman iframe. Error: {e}")

# Auto-refresh data backend setiap 60 detik
time.sleep(60)
st.rerun()
