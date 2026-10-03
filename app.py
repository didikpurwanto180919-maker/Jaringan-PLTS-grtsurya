import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Monitoring PLTS Grt Surya", layout="wide"
)

st.title("Dashboard Monitoring PLTS Grt Surya")
st.info("Pastikan perangkat Anda terhubung ke jaringan internal/lokal kantor.")

# Menyematkan dashboard internal
components.iframe(
    "http://grtsurya.indonesiapower.co.id:82/", height=800, scrolling=True
)
