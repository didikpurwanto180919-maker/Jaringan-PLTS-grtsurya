import requests
import streamlit as st

st.set_page_config(page_title="Monitoring PLTS Grt Surya", layout="wide")
st.title("Dashboard Monitoring PLTS Grt Surya")

try:
  # Contoh mengambil data dari API dashboard internal (sesuaikan endpoint-nya)
  response = requests.get(
      "http://grtsurya.indonesiapower.co.id:82/api/data", timeout=5
  )

  if response.status_code == 200:
    data = response.json()

    # Tampilkan data dalam bentuk komponen Streamlit yang bersih
    col1, col2 = st.columns(2)
    with col1:
      st.metric(label="Daya Output Inverter", value=f"{data.get('power', 0)} kW")
    with col2:
      st.metric(label="Status Sistem", value=data.get("status", "Normal"))
  else:
    st.warning("Server merespons, tetapi data gagal dimuat.")

except Exception as e:
  st.error(
      "Tidak dapat mengambil data dari server lokal. Pastikan terhubung ke"
      " jaringan internal."
  )
  st.markdown(
      "🔗 [Buka Dashboard Langsung di Tab"
      " Baru](http://grtsurya.indonesiapower.co.id:82/)"
  )
