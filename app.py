import streamlit as st
import requests
from bs4 import BeautifulSoup

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Monitoring PLTS Grati 1.5 MWp",
    page_icon="☀️",
    layout="wide"
)

st.title("☀️ Monitoring PLTS Grati POMU 1.5 MWp")

# Input URL Ngrok dari Sidebar agar mudah diubah tanpa edit kode
st.sidebar.header("Konfigurasi Koneksi")
url_ngrok = st.sidebar.text_input(
    "Masukkan URL Ngrok Lokal:", 
    placeholder="https://xxxx-xxx-xxx.ngrok-free.app"
)

st.sidebar.info(
    "💡 **Petunjuk:**\n"
    "1. Jalankan `ngrok http http://grtsurya.indonesiapower.co.id:82` di CMD PC lokal PLTS.\n"
    "2. Salin URL publik dari Ngrok ke kolom di atas."
)

headers = {
    "User-Agent": "Mozilla/5.0",
    "ngrok-skip-browser-warning": "69420"  # Bypass halaman konfirmasi ngrok
}

@st.cache_data(ttl=30)  # Refresh data setiap 30 detik
def ambil_data_plts(target_url):
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text, None
        else:
            return None, f"HTTP Status Code: {response.status_code}"
    except Exception as e:
        return None, str(e)

if url_ngrok:
    html_content, error_msg = ambil_data_plts(url_ngrok)
    
    if error_msg:
        st.error(f"❌ Gagal Terhubung ke Server PLTS: {error_msg}")
        st.warning("Pastikan Ngrok dan PC lokal di jaringan PLTS masih aktif.")
    else:
        st.success("✅ Terhubung ke Dasbor PLTS Grati!")
        
        # Parse HTML menggunakan BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Tampilan Ringkasan dengan Tabs
        tab1, tab2 = st.tabs(["📊 Dasbor Tampilan", "🔍 Mentah / Debug HTML"])
        
        with tab1:
            st.subheader("Ringkasan Parameter Operasional")
            
            # Baris Metrik Utama (Contoh layout kartu)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Status Jaringan", value="On-Grid")
            with col2:
                st.metric(label="Kapasitas String", value="1507.00 kWp")
            with col3:
                st.metric(label="Frekuensi AC", value="49.98 Hz")
            with col4:
                st.metric(label="Suhu Lingkungan", value="28.50 °C")
                
            st.write("---")
            st.info("ℹ️ Tampilan data mentah berhasil ditarik dari jaringan lokal PLTS.")

        with tab2:
            st.subheader("Struktur HTML Halaman Dasbor")
            st.text_area("Isi HTML Terambil", value=soup.prettify()[:2000], height=300)
else:
    st.warning("⚠️ Silakan masukkan URL Ngrok pada panel di sebelah kiri (sidebar) untuk mulai menampilkan data.")
