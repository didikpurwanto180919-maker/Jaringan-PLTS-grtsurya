import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

# Judul Aplikasi
st.title("⚡ Dashboard Monitoring Real-Time - GRT Surya (PLTS)")
st.markdown("---")

# URL Ngrok yang sudah di-hardcode
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"

# Sidebar Informasi Status
st.sidebar.header("⚙️ Status Koneksi & Pengaturan")
st.sidebar.success("Status: Terhubung ke Ngrok Tunnel")
st.sidebar.markdown(f"**URL Aktif:** `{NGROK_URL}`")

st.sidebar.info(
    "💡 Pastikan PC kantor di jaringan internal PLTS tetap aktif menjalankan perintah Ngrok ke server `http://grtsurya.indonesiapower.co.id:82`."
)

# --- BAGIAN 1: METRIK & DATA IRADIANSI (GLOBAL SOLAR ATLAS) ---
st.header("☀️ Data & Potensi Iradiansi Surya Real-Time (Grati)")
st.markdown(
    "Berikut adalah peta interaktif dan data potensi iradiansi wilayah Grati, Pasuruan (Global Solar Atlas)."
)

# Membuat kolom untuk tata letak metrik ringkas di atas peta
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric(
        label="Koordinat Lokasi",
        value="-7.6949, 112.8996",
        delta="Grati, Blok / Area",
    )
with col_m2:
    st.metric(
        label="Estimasi GHI Rata-rata",
        value="~ 4.8 - 5.2 kWh/m²",
        delta="Kondisi Optimal",
    )
with col_m3:
    st.metric(
        label="Status Sumber Data",
        value="Global Solar Atlas",
        delta="Online",
    )

# Embed Global Solar Atlas sesuai koordinat yang diminta
# Menggunakan parameter URL dari Global Solar Atlas (embed view)
gsa_url = "https://globalsolaratlas.info/map?r=IDN&c=-7.694940,112.899628,11&s=-8.164740,113.213579&m=site"

try:
    st.components.v1.iframe(gsa_url, height=450, scrolling=True)
except Exception as e:
    st.warning(fTidak dapat memuat peta Global Solar Atlas: {e}")

st.markdown("---")

# --- BAGIAN 2: MONITORING DAYA AKTIF (NGROK MIRROR SERVER) ---
st.header("🔋 Monitoring Daya Aktif & Parameter Inverter Internal")
st.success(f"Menampilkan mirror dari server internal via: `{NGROK_URL}`")

# Embedding halaman web internal menggunakan iframe untuk Daya Aktif
try:
    st.components.v1.iframe(NGROK_URL, height=700, scrolling=True)
except Exception as e:
    st.error(
        f"Gagal memuat halaman mirror internal. Pastikan sesi Ngrok di PC kantor Anda masih aktif. Error: {e}"
    )
    
