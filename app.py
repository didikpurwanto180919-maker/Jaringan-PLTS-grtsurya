import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PR & Monitoring PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

# Judul Utama Aplikasi
st.title("⚡ Dashboard Monitoring & Performance Ratio (PR) GRT Surya - PLTS")
st.markdown("---")

# URL Ngrok dan Global Solar Atlas yang dikonfigurasi
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"
SOLAR_ATLAS_URL = "https://globalsolaratlas.info/map?c=-7.678604,112.905121,11&s=-7.649007,113.025970&m=site"

# Sidebar Informasi Status
st.sidebar.header("⚙️ Status Koneksi & Sistem")
st.sidebar.success("Status: Terhubung ke Ngrok & Global Solar Atlas")
st.sidebar.markdown(f"**URL Mirror Aktif:** `{NGROK_URL}`")

st.sidebar.info(
    "💡 Pastikan PC kantor di jaringan internal PLTS tetap aktif menjalankan perintah Ngrok ke server lokal."
)

# --- BAGIAN 1: METRIK UTAMA & PERFORMANCE RATIO (PR) REAL-TIME ---
st.subheader("📊 Ringkasan Parameter & Performance Ratio (PR)")

# Membuat 4 kolom untuk metrik utama (Anda bisa menyesuaikan nilainya atau menghubungkannya ke API/data real-time server internal)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Daya Aktif (Active Power)", value="-- kW", delta="Real-time")

with col2:
    st.metric(label="Iradiance Global (GTI)", value="-- W/m²", delta="Live Data")

with col3:
    st.metric(label="Performance Ratio (PR)", value="-- %", delta="Target > 80%")

with col4:
    st.metric(label="Temperatur Modul", value="-- °C", delta="Normal")

st.markdown("---")

# --- BAGIAN 2: TAMPILAN DUA KOLOM (GLOBAL SOLAR ATLAS & MIRROR SERVER) ---
col_left, col_right = st.columns(2)

# Kolom Kiri: Iradiance & Peta Global Solar Atlas
with col_left:
    st.subheader("🌍 Real-time Iradiance & Peta Solar (Global Solar Atlas)")
    st.markdown(
        "Menampilkan data radiasi surya dan parameter lokasi PLTS Grati."
    )
    try:
        # Menggunakan iframe untuk memuat peta Global Solar Atlas pada koordinat yang ditentukan
        st.components.v1.iframe(
            SOLAR_ATLAS_URL, height=600, scrolling=True
        )
    except Exception as e:
        st.error(f"Gagal memuat Global Solar Atlas. Error: {e}")

# Kolom Kanan: Mirror Server Internal (Daya Aktif & Monitoring Sistem)
with col_right:
    st.subheader("🖥️ Monitoring Daya Aktif (Server Internal PLTS)")
    st.markdown(
        f"Menampilkan mirror langsung dari server internal via: `{NGROK_URL}`"
    )
    try:
        # Embedding halaman web internal menggunakan iframe
        st.components.v1.iframe(NGROK_URL, height=600, scrolling=True)
    except Exception as e:
        st.error(
            f"Gagal memuat halaman mirror. Pastikan sesi Ngrok aktif. Error: {e}"
        )

# Footer info tambahan
st.markdown("---")
st.caption(
    "PLTS Grati Monitoring System | Dikembangkan dengan Streamlit untuk Operasional Pembangkit."
)
