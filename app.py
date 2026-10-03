import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Dashboard Monitoring PLTS Grt Surya", layout="wide")

st.title("Dashboard Monitoring PLTS Grt Surya")

# Masukkan link HTTPS dari ngrok ke dalam tanda kutip di bawah ini:
ngrok_url = "https://xxxx-xxxx.ngrok-free.app"

components.iframe(ngrok_url, height=850, scrolling=True)
