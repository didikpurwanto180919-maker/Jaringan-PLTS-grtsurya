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

# URL Ngrok yang sudah di-hardcode
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"

# Sidebar Informasi Status
st.sidebar.header("⚙️ Status Koneksi")
st.sidebar.success("Status: Terhubung ke Ngrok Tunnel")
st.sidebar.markdown(f"**URL Aktif:** `{NGROK_URL}`")

st.sidebar.info(
    "💡 Pastikan PC kantor di jaringan internal PLTS tetap aktif menjalankan perintah Ngrok ke server `http://grtsurya.indonesiapower.co.id:82`."
)

# Main Content
st.success(f"Menampilkan mirror dari server internal via: `{NGROK_URL}`")

# Embedding halaman web internal menggunakan iframe
try:
    st.components.v1.iframe(NGROK_URL, height=800, scrolling=True)
except Exception as e:
    st.error(
        f"Gagal memuat halaman. Pastikan sesi Ngrok di PC kantor Anda masih aktif. Error: {e}"
    )
