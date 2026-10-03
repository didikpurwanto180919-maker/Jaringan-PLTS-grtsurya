import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Dashboard Monitoring PLTS Grt Surya", layout="wide")

st.title("Dashboard Monitoring PLTS Grt Surya")
st.info(
    "Menampilkan dashboard internal secara langsung (Mirroring via Jaringan"
    " Lokal)."
)

# Menyematkan dashboard internal secara utuh dalam satu layar
components.iframe(
    "http://grtsurya.indonesiapower.co.id:82/", height=850, scrolling=True
)
