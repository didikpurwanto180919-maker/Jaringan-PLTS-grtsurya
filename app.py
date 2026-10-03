import streamlit as st
import requests
import pandas as pd

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Monitoring PLTS - GRT Surya",
    page_icon="☀️",
    layout="wide"
)

st.title("☀️ Dashboard Monitoring PLTS")
st.markdown("Menghubungkan Streamlit ke server internal: `http://grtsurya.indonesiapower.co.id:82/`")

# Sidebar untuk pengaturan / tombol refresh
st.sidebar.header("Pengaturan Koneksi")
api_url = st.sidebar.text_input(
    "URL API Target", 
    value="http://grtsurya.indonesiapower.co.id:82/"
)
refresh_btn = st.sidebar.button("Muat Ulang Data")

# Fungsi untuk mengambil data dari server
def fetch_plts_data(url):
    try:
        # Mengirim request GET ke server (dengan timeout 5 detik)
        response = requests.get(url, timeout=5)
        
        # Cek apakah request berhasil (status 200)
        if response.status_code == 200:
            # Jika server mengembalikan JSON
            try:
                return response.json(), "json"
            except ValueError:
                # Jika server mengembalikan teks biasa / HTML
                return response.text, "text"
        else:
            return f"Error: Server merespons dengan status code {response.status_code}", "error"
            
    except requests.exceptions.ConnectionError:
        return "Gagal terhubung! Pastikan Anda sudah terhubung ke jaringan internal / VPN perusahaan.", "error"
    except requests.exceptions.Timeout:
        return "Waktu koneksi habis (Timeout). Server terlalu lama merespons.", "error"
    except Exception as e:
        return fTerjadi kesalahan: {str(e)}", "error"

# Main Content
with st.spinner("Menghubungkan ke server GRT Surya..."):
    result, data_type = fetch_plts_data(api_url)

if data_type == "json":
    st.success("Berhasil terhubung dan mendapatkan data JSON dari server!")
    st.json(result)
    
    # Contoh jika data JSON berupa list/dictionary yang bisa diubah ke DataFrame Pandas
    # if isinstance(result, list):
    #     df = pd.DataFrame(result)
    #     st.dataframe(df)

elif data_type == "text":
    st.warning("Server merespons, tetapi format data bukan JSON. Berikut isi teks/HTML dari server:")
    st.text_area("Respon Server", result, height=300)

else:
    st.error(result)
    st.info(
        "**Tips Troubleshooting:**\n"
        "1. Pastikan komputer Anda terhubung ke jaringan lokal (LAN) PLTS / Indonesia Power.\n"
        "2. Jika akses dari luar kantor, pastikan VPN perusahaan sudah aktif.\n"
        "3. Cek apakah port `:82` diizinkan oleh firewall komputer Anda."
    )
