import os
import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

# Judul Aplikasi
st.title("⚡ Dashboard Monitoring GRT Surya - PLTS")
st.markdown("---")

# Mengatur Authtoken Ngrok secara otomatis dari kode
NGROK_AUTH_TOKEN = "3IgKMhfPKRux6o3FF7im5WfcwRW_aZnMxYB1p5XGSDrgEykM"
TARGET_URL = "http://grtsurya.indonesiapower.co.id:82"

# Sidebar untuk informasi status
st.sidebar.header("⚙️ Status Koneksi")
st.sidebar.info(f"Target Internal: `{TARGET_URL}`")

# Peringatan jika dijalankan di Streamlit Cloud (karena Streamlit Cloud tidak bisa menjangkau jaringan lokal perusahaan secara langsung)
st.sidebar.warning(
    "💡 Catatan: Jika aplikasi ini di-deploy ke Streamlit Cloud (publik), "
    "koneksi ke `indonesiapower.co.id` hanya bisa dilakukan jika aplikasi ini "
    "dijalankan secara lokal di komputer dalam jaringan pembangkit."
)

# Main Content
st.success(f"Menghubungkan ke server internal via Ngrok...")

# Embedding halaman web internal menggunakan iframe
try:
    # Jika Anda menjalankan skrip ini secara lokal di PC kantor:
    # Anda bisa langsung menggunakan URL target atau URL ngrok yang terhubung
    st.components.v1.iframe(TARGET_URL, height=800, scrolling=True)
except Exception as e:
    st.error(
        f"Gagal memuat halaman. Pastikan komputer Anda terhubung ke jaringan internal PLTS. Error: {e}"
    )
