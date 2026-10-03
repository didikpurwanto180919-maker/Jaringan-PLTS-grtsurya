import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Monitoring PLTS Grt Surya", layout="wide")

st.title("Dashboard Monitoring PLTS Grt Surya")
st.info("Pastikan perangkat Anda terhubung ke jaringan internal/lokal kantor.")

# Tombol alternatif jika iframe diblokir browser
st.markdown(
    "🔗 Jika dashboard di bawah tidak muncul, buka langsung di tab baru:"
    " [Klik di Sini](http://grtsurya.indonesiapower.co.id:82/)",
    unsafe_allow_html=True,
)

# Menyematkan dashboard internal
components.iframe(
    "http://grtsurya.indonesiapower.co.id:82/", height=800, scrolling=True
)
