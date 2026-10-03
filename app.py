import streamlit as st

st.set_page_config(
    page_title="Portal Monitoring PLTS Grt Surya", layout="wide"
)

st.title("☀️ Portal Dashboard Monitoring PLTS Grt Surya")
st.info(
    "ℹ️ Pastikan perangkat Anda sudah terhubung ke jaringan internal / LAN"
    " kantor PLTGU/PLTS Grati."
)

st.write("---")

# Tombol interaktif untuk membuka dashboard lokal
st.markdown(
    "### Klik tombol di bawah untuk membuka dashboard monitoring secara"
    " langsung:"
)
st.link_button(
    "🚀 Buka Dashboard GRT Surya", "http://grtsurya.indonesiapower.co.id:82/"
)

st.write("")
st.caption(
    "Catatan: Dashboard ini menggunakan jaringan lokal kantor dan tidak dapat"
    " dimuat langsung di dalam halaman cloud demi alasan keamanan jaringan"
    " perusahaan."
)
