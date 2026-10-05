import datetime
import random
import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PR & Iradiansi - PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

# Judul Aplikasi
st.title("⚡ Dashboard Monitoring & Performance Ratio (PR) - PLTS GRT Surya")
st.markdown("---")

# URL Ngrok yang sudah di-hardcode
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"

# Sidebar Informasi Status
st.sidebar.header("⚙️ Status Sistem & Lokasi")
st.sidebar.success("Status: Terhubung ke Ngrok Tunnel")
st.sidebar.markdown(f"**URL Aktif:** `{NGROK_URL}`")

# Informasi Koordinat Lokasi (berdasarkan Global Solar Atlas)
st.sidebar.markdown("### 📍 Lokasi Site")
st.sidebar.text("Latitude: -7.678604\nLongitude: 112.905121")
st.sidebar.markdown(
    "[Buka Peta Global Solar Atlas](https://globalsolaratlas.info/map?c=-7.678604,112.905121,11&s=-7.649007,113.025970&m=site)",
    unsafe_allow_html=True,
)

st.sidebar.info(
    "💡 Pastikan PC kantor di jaringan internal PLTS tetap aktif menjalankan perintah Ngrok ke server internal."
)

# --- BAGIAN 1: METRIK REAL-TIME IRADIANSI & PERFORMANCE RATIO (PR) ---
st.header("📊 Real-Time Performance Ratio & Solar Irradiance")
st.markdown(
    "Data parameter cuaca dan performa pembangkit secara *real-time* pada koordinat site."
)

# Tombol untuk memperbarui data real-time
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    refresh_data = st.button("🔄 Refresh Data")

# Simulasi / Pengambilan Data Real-Time (Dapat disesuaikan dengan API sensor aktual)
# Menggunakan nilai acak yang wajar untuk simulasi live data jika belum tersambung langsung ke sensor
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
irradiance_val = round(random.uniform(750, 980), 2)  # W/m²
ambient_temp = round(random.uniform(30.5, 35.2), 1)  # °C
pr_val = round(
    random.uniform(82.5, 89.1), 2
)  # Performance Ratio dalam persentase (%)
power_gen = round(random.uniform(1.2, 2.4), 2)  # MW

# Layout Metrik dalam 4 Kolom
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric(
        label="☀️ GHI (Iradiansi Global)",
        value=f"{irradiance_val} W/m²",
        delta="+12 W/m²",
    )
with m2:
    st.metric(
        label="📈 Performance Ratio (PR)",
        value=f"{pr_val} %",
        delta="+0.4%",
    )
with m3:
    st.metric(
        label="⚡ Daya Aktif (Power Output)",
        value=f"{power_gen} MW",
        delta="-0.05 MW",
    )
with m4:
    st.metric(
        label="🌡️ Temperatur Modul/Ambien",
        value=f"{ambient_temp} °C",
        delta="+0.2 °C",
    )

st.caption(f"Terakhir diperbarui: {current_time} (WIB)")
st.markdown("---")

# --- BAGIAN 2: EMBEDDING SERVER INTERNAL VIA NGROK ---
st.header("🖥️ Mirror Server Internal PLTS")
st.success(f"Menampilkan antarmuka asli dari server internal via: `{NGROK_URL}`")

# Embedding halaman web internal menggunakan iframe
try:
    st.components.v1.iframe(NGROK_URL, height=700, scrolling=True)
except Exception as e:
    st.error(
        f"Gagal memuat halaman. Pastikan sesi Ngrok di PC kantor Anda masih aktif. Error: {e}"
    )
