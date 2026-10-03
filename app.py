import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Dashboard Monitoring PLTS Grt Surya", layout="wide")

st.title("Dashboard Monitoring PLTS Grt Surya")

# Ganti tulisan di dalam tanda kutip di bawah ini dengan link Forwarding HTTPS dari Ngrok Anda:
ngrok_url = "https://masukkan-link-asli-dari-ngrok.ngrok-free.app"

components.iframe(ngrok_url, height=850, scrolling=True)
