import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Dashboard Monitoring GRT Surya - PLTS")
st.markdown("---")

# Sidebar untuk input URL Ngrok dinamis
st.sidebar.header("⚙️ Konfigurasi Koneksi Ngrok")
ngrok_url = st.sidebar.text_input(
    "Masukkan URL Ngrok aktif dari PC Kantor:",
    value="",
    placeholder="https://xxxx.ngrok-free.app",
)

st.sidebar.info(
    "💡 Pastikan PC di jaringan internal PLTS sedang menjalankan `ngrok http http://grtsurya.indonesiapower.co.id:82`."
)

# Main Content
if not ngrok_url:
    st.warning(
        "⚠️ Silakan masukkan **URL Ngrok** aktif pada kolom di sidebar sebelah kiri untuk menampilkan dashboard."
    )
else:
    st.success(f"Menampilkan mirror dari server internal via: `{ngrok_url}`")
    try:
        st.components.v1.iframe(ngrok_url, height=800, scrolling=True)
    except Exception as e:
        st.error(f"Gagal memuat iframe. Error: {e}")
