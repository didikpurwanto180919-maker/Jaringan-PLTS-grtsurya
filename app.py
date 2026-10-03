import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Jaringan PLTS GRT Surya - Monitoring",
    page_icon="⚡",
    layout="wide"
)

# Header Utama
st.title("⚡ Jaringan PLTS GRT Surya")
st.markdown("Dashboard integrasi monitoring real-time dari server internal perusahaan.")

# Sidebar untuk Informasi dan Konfigurasi Tunnel
st.sidebar.header("Konfigurasi Koneksi")
st.sidebar.info(
    "Pastikan agen **Ngrok** aktif di komputer lokal yang terhubung ke jaringan internal PLTS "
    "(`http://grtsurya.indonesiapower.co.id:82/`)."
)

# Input Dinamis untuk URL Ngrok Aktif (atau bisa di-hardcode jika tetap)
ngrok_url = st.sidebar.text_input(
    "Masukkan URL Publik Ngrok Terbaru:",
    value="https://xxxx-xx-xx.ngrok-free.app",
    help="Salin URL HTTPS yang dihasilkan oleh terminal ngrok Anda di sini."
)

st.sidebar.divider()
st.sidebar.subheader("Panduan Singkat:")
st.sidebar.markdown(
    """
    1. Buka terminal di PC lokal (jaringan PLTS).
    2. Jalankan: `ngrok http http://grtsurya.indonesiapower.co.id:82`
    3. Salin URL `https://...ngrok-free.app` yang muncul.
    4. Tempelkan URL tersebut ke kolom di atas.
    """
)

# Area Utama Aplikasi
if ngrok_url and "ngrok-free.app" in ngrok_url:
    st.success(Menampilkan mirror dari server internal via: `{ngrok_url}`)
    
    # Menampilkan web server internal menggunakan komponen iframe Streamlit
    try:
        st.components.v1.iframe(
            src=ngrok_url, 
            height=750, 
            scrolling=True
        )
    except Exception as e:
        st.error(f"Gagal memuat iframe. Periksa kembali koneksi atau URL ngrok Anda. Error: {e}")
else:
    st.warning("⚠️ Masukkan URL Ngrok yang valid pada panel sebelah kiri untuk memuat dashboard.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Maker Jaringan PLTS GRT Surya App &copy; 2026</p>", unsafe_allow_html=True)
