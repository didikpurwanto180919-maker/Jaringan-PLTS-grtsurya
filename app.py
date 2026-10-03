import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st
import time

st.set_page_config(
    page_title="Monitoring GRT Surya - Streamlit",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Monitoring Grati 1.5 MWp Land-based Bifacial PV")
st.write("Menghubungkan data dari `http://grtsurya.indonesiapower.co.id:82/`")


# Fungsi untuk mengambil data
@st.cache_data(ttl=60)  # Cache data selama 60 detik agar tidak spam request
3
def fetch_data():
  url = "http://grtsurya.indonesiapower.co.id:82/"
  try:
    # Mengambil konten halaman web
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    # Opsi 1: Jika data berupa tabel HTML di dalam halaman
    # pandas.read_html akan otomatis mencari tag <table> dan mengubahnya jadi dataframe
    tables = pd.read_html(response.text)
    if tables:
      return tables[
          0
      ], None  # Mengambil tabel pertama yang ditemukan di halaman

    return None, "Tidak ditemukan tabel data pada halaman tersebut."

  except Exception as e:
    return None, str(e)


# Tombol Refresh Manual
if st.button("Refresh Data"):
  st.cache_data.clear()

# Memuat data
with st.spinner("Mengambil data dari server Grt Surya..."):
  df, error = fetch_data()

if error:
  st.error(
      f"Gagal terhubung ke server: {error}. Pastikan Anda terhubung ke jaringan"
      " internal / VPN Indonesia Power."
  )
else:
  st.success("Berhasil terhubung ke server!")

  # Tampilkan metrik atau ringkasan jika ada kolom tertentu
  st.subheader("Data Monitoring Terkini")
  st.dataframe(df, use_container_width=True)

  # Contoh visualisasi sederhana jika ada kolom numerik
  # st.line_chart(df['Nama_Kolom_Daya'])
