import time
import requests
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PLTS GRT Surya & SCADA",
    page_icon="⚡",
    layout="wide",
)

# Judul Aplikasi
st.title("⚡ Live Dashboard Monitoring, AI Early Warning & SCADA Mirror")

# --- WIDGET JAM REAL-TIME BERDETAK (JAVASCRIPT) ---
clock_html = """
<div style="font-family: monospace; font-size: 16px; font-weight: bold; color: #2e7d32; background-color: #e8f5e9; padding: 8px; border-radius: 5px; display: inline-block;">
    📅 Waktu Realtime: <span id="live-clock"></span>
</div>
<script>
function updateClock() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false };
    document.getElementById('live-clock').innerText = now.toLocaleDateString('id-ID', options);
}
setInterval(updateClock, 1000);
updateClock();
</script>
"""
components.html(clock_html, height=45)
st.markdown("---")

# URL Ngrok sumber data/SCADA internal (Menuju http://grtsurya.indonesiapower.co.id:82/)
NGROK_URL = "https://reveler-striking-feminist.ngrok-free.dev"

# Koordinat Global Solar Atlas PLTS Grati
LATITUDE = -7.678604
LONGITUDE = 112.905121

# Sidebar Konfigurasi Sistem
st.sidebar.header("⚙️ Status & Konfigurasi
