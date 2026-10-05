import random  # Simulasi pembacaan live sensor jika belum ada API endpoint langsung
import time
import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

# Judul Aplikasi
st.title("⚡ Dashboard Monitoring & Performance Ratio (PR) GRT Surya - PLTS")
st.markdown("---")

# URL Ngrok yang sudah di-hardcode
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"

# Sidebar untuk Parameter Konfigurasi PLTS & PR
st.sidebar.header("⚙️ Konfigurasi Sistem & PR")
st.sidebar.success("Status: Terhubung ke Ngrok Tunnel")
st.sidebar.markdown(f"**URL Aktif:** `{NGROK_URL}`")

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Parameter Kalkulasi PR")
# Kapasitas terpasang PLTS (P_peak dalam kWp) - sesuaikan dengan kapasitas eksisting PLTGU Grati
installed_capacity = st.sidebar.number_input(
    "Kapasitas Terpasang (kWp / MWp konversi)",
    min_value=100.0,
    max_value=50000.0,
    value=1000.0,
    step=50.0,
)
st_cnd_irradiance = 1000.0  # W/m² standar STC

st.sidebar.info(
    "💡 Modul PR menghitung efisiensi sistem secara realtime dengan membandingkan Active Power aktual terhadap Irradiance global."
)

# Simulasi / Pengambilan Nilai Realtime (Dapat dihubungkan ke API SCADA/Inverter Anda)
# Untuk keperluan demo live dashboard, kita sediakan state/simulasi pembacaan live atau input data
col_sim1, col_sim2 = st.columns(2)
with col_sim1:
    # Contoh pembacaan Active Power (kW) - bisa diganti parsing dari Ngrok / SCADA
    active_power_realtime = st.slider(
        "Simulasi Active Power Realtime (kW)",
        min_value=0.0,
        max_value=installed_capacity,
        value=650.0,
    )
with col_sim2:
    # Contoh pembacaan Irradiance (W/m²) - referensi lokasi Grati / Global Solar Atlas
    irradiance_realtime = st.slider(
        "Simulasi Irradiance Realtime (W/m²)",
        min_value=0.0,
        max_value=1200.0,
        value=850.0,
    )

# --- Perhitungan Performance Ratio (PR) ---
if irradiance_realtime > 0:
    # Rumus PR = [P_ac / P_peak] / [Irradiance / 1000]
    expected_power = installed_capacity * (irradiance_realtime / st_cnd_irradiance)
    performance_ratio = (
        (active_power_realtime / expected_power) * 100
        if expected_power > 0
        else 0.0
    )
else:
    performance_ratio = 0.0

st.markdown("### 📊 Indikator Kinerja Realtime (PR)")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Active Power (P_ac)", f"{active_power_realtime:.2f} kW")
m2.metric("Solar Irradiance (G)", f"{irradiance_realtime:.1f} W/m²")
m3.metric("Kapasitas Terpasang", f"{installed_capacity:.1f} kWp")
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
    st.components.v1.iframe(NGROK_URL, height=700, scrolling=True)
except Exception as e:
    st.error(
        f"Gagal memuat halaman. Pastikan sesi Ngrok di PC kantor Anda masih aktif. Error: {e}"
    )
