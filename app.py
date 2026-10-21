import time
import urllib.parse
import requests
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from datetime import datetime

# Import pustaka Machine Learning
from sklearn.linear_model import LinearRegression
try:
    from xgboost import XGBRegressor
    ML_MODEL_TYPE = "XGBoost Regressor"
except ImportError:
    from sklearn.ensemble import RandomForestRegressor as XGBRegressor
    ML_MODEL_TYPE = "RandomForest (Fallback)"

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="PRO-BIFACIAL ML & Soiling Early Warning - PLTS 1.5 MWp",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ PRO-BIFACIAL ML: Performance Ratio Optimization & AI Soiling Early Warning")

# --- WIDGET JAM REAL-TIME ---
clock_html = """
<div style="font-family: monospace; font-size: 15px; font-weight: bold; color: #1b5e20; background-color: #e8f5e9; padding: 6px 12px; border-radius: 6px; display: inline-block;">
    📅 Waktu Sistem: <span id="live-clock"></span>
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

# --- INISIALISASI SESSION STATE ---
BASELINE_DEFAULT = 82.5  # %

if "baseline_pr" not in st.session_state:
    st.session_state.baseline_pr = BASELINE_DEFAULT

if "cleaning_scheduled" not in st.session_state:
    st.session_state.cleaning_scheduled = False

if "last_wa_alert_time" not in st.session_state:
    st.session_state.last_wa_alert_time = 0.0

if "historical_df" not in st.session_state:
    history_data = {
        "Hari_Ke": [1, 2, 3, 4, 5, 6, 7],
        "Tanggal": [
            "2026-10-15", "2026-10-16", "2026-10-17", 
            "2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21"
        ],
        "POA_kWh_m2": [5.1, 2.3, 5.2, 5.0, 5.1, 4.9, 5.0],
        "Suhu_Modul_C": [47.5, 31.0, 48.2, 47.0, 48.0, 46.8, 47.2],
        "Actual_PR": [82.1, 79.2, 77.4, 75.8, 74.0, 72.3, 71.1],
        "PR_Terkoreksi": [82.4, 80.1, 77.9, 76.1, 74.3, 72.8, 71.5],
        "Cuaca": ["Cerah", "Hujan/Mendung", "Cerah", "Cerah", "Cerah", "Cerah", "Cerah"],
        "Anomali_Cuaca": [False, True, False, False, False, False, False]
    }
    st.session_state.historical_df = pd.DataFrame(history_data)

# --- SIDEBAR KONFIGURASI SISTEM & WHATSAPP ---
st.sidebar.header("⚙️ Konfigurasi Sistem PLTS")
installed_capacity = st.sidebar.number_input("Kapasitas Terpasang (kWp)", value=1500.0, step=50.0)[cite: 1]
stc_irradiance = 1000.0  # W/m²[cite: 1]
gamma_pmax = st.sidebar.number_input("Koefisien Suhu Pmax (%/°C)", value=-0.38, step=0.01) / 100.0
stc_temp = 25.0
tariff_per_kwh = st.sidebar.number_input("Tarif Listrik (IDR/kWh)", value=1445, step=50)

st.sidebar.markdown("---")
st.sidebar.subheader("📱 Konfigurasi Alarm WhatsApp")
wa_phone_number = st.sidebar.text_input(
    "Nomor WhatsApp Target / Operator", 
    value="6281234567890",
    help="Gunakan kode negara tanpa tanda plus (+), contoh: 6281234567890"
)
fonnte_token = st.sidebar.text_input(
    "Fonnte API Token (Opsional)", 
    value="", 
    type="password",
    help="Masukkan token Fonnte jika ingin notifikasi terkirim otomatis di latar belakang."
)
auto_send_enabled = st.sidebar.checkbox("Aktifkan Auto-Send Alarm (Cooldown 1 Jam)", value=False)

NGROK_URL = st.sidebar.text_input(
    "🔗 Endpoint Mirror SCADA Ngrok", 
    value="https://reveler-striking-feminist.ngrok-free.dev"[cite: 1]
)

# --- ENGINE MACHINE LEARNING: BENCHMARK MODUL BERSIH ---
@st.cache_resource
def train_clean_benchmark_model():
    np.random.seed(42)
    poa_samples = np.random.uniform(2.5, 6.5, 150)
    temp_samples = 25.0 + (poa_samples * 4.4) + np.random.normal(0, 1.2, 150)
    pr_clean_ideal = 82.5 - (0.0038 * (temp_samples - 25.0) * 8.0) + np.random.normal(0, 0.35, 150)
    
    X_synth = np.column_stack((poa_samples, temp_samples))
    y_synth = pr_clean_ideal
    
    model = XGBRegressor(n_estimators=60, max_depth=3, learning_rate=0.08, random_state=42)
    model.fit(X_synth, y_synth)
    return model

ml_clean_model = train_clean_benchmark_model()

# --- ENGINE AKUISISI TELEMETRI REAL-TIME ---
def get_current_telemetry():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    micro = np.sin(minute * np.pi / 30) * 0.15[cite: 1]

    if 6 <= hour <= 17:
        base_power = max(0.5, 3.5 - abs(hour - 12) * 0.4) + micro[cite: 1]
        poa = max(50.0, 820.0 - abs(hour - 12) * 115.0)
    else:
        base_power = 0.0[cite: 1]
        poa = 0.0[cite: 1]

    t_mod = 31.0 + (np.sin(hour * np.pi / 24) * 18.0)
    total_power = 0.0[cite: 1]
    inverters = []

    for i in range(1, 13):
        cap = 128.4 if i <= 11 else 87.6[cite: 1]
        p = round(max(0.0, (base_power + (i * 0.02) if i <= 11 else base_power - 0.75)), 2)[cite: 1]
        inverters.append({"id": i, "name": f"Inverter {i:02d}", "power": p, "capacity": cap})[cite: 1]
        total_power += p[cite: 1]

    return total_power, poa, t_mod, inverters

p_total, poa_realtime, t_module, inverters_list = get_current_telemetry()

# Formulasi PR Standar & PR Terkoreksi Suhu (IEC 61724)
if poa_realtime > 0:
    p_expected_stc = installed_capacity * (poa_realtime / stc_irradiance)[cite: 1]
    pr_actual = (p_total / p_expected_stc) * 100.0 if p_expected_stc > 0 else 0.0[cite: 1]
    temp_factor = 1.0 + gamma_pmax * (t_module - stc_temp)
    pr_temp_corrected = pr_actual / temp_factor if temp_factor != 0 else pr_actual
else:
    p_expected_stc = 0.0
    pr_actual = 0.0[cite: 1]
    pr_temp_corrected = 0.0

# --- INFERENSI ML & PROYEKSI LAJU DEBU ---
df_hist = st.session_state.historical_df.copy()
X_eval = df_hist[["POA_kWh_m2", "Suhu_Modul_C"]].values
df_hist["ML_Predicted_Clean_PR"] = ml_clean_model.predict(X_eval)
df_hist["Soiling_Loss_Pct"] = np.maximum(0.0, df_hist["ML_Predicted_Clean_PR"] - df_hist["PR_Terkoreksi"])

clean_weather_days = df_hist[~df_hist["Anomali_Cuaca"]]
reg = LinearRegression()
reg.fit(clean_weather_days[["Hari_Ke"]], clean_weather_days["PR_Terkoreksi"])
daily_soiling_rate = -float(reg.coef_[0])

critical_threshold = st.session_state.baseline_pr * 0.90
latest_pr = df_hist.iloc[-1]["PR_Terkoreksi"]
latest_clean_benchmark = df_hist.iloc[-1]["ML_Predicted_Clean_PR"]
current_soiling_loss = df_hist.iloc[-1]["Soiling_Loss_Pct"]

if daily_soiling_rate > 0.01:
    days_to_critical = int(np.ceil((latest_pr - critical_threshold) / daily_soiling_rate))
    days_to_critical = max(0, days_to_critical)
else:
    days_to_critical = 99

future_days = np.array([[8], [9], [10]])
future_pr_forecast = reg.predict(future_days)

# Status & Alert Logic
if latest_pr <= critical_threshold:
    alert_level = "CRITICAL"
    status_label = "Kritis (Pembersihan Diperlukan)"
elif current_soiling_loss >= (st.session_state.baseline_pr * 0.05):
    alert_level = "WARNING"
    status_label = "Perlu Dijadwalkan Pembersihan"
else:
    alert_level = "NORMAL"
    status_label = "Modul Bersih / Beroperasi Optimal"

daily_insol_kwh_m2 = 5.0
e_ideal_clean = installed_capacity * daily_insol_kwh_m2 * (latest_clean_benchmark / 100.0)
e_actual_proj = installed_capacity * daily_insol_kwh_m2 * (latest_pr / 100.0)
daily_energy_loss_kwh = max(0.0, e_ideal_clean - e_actual_proj)
daily_revenue_loss_idr = daily_energy_loss_kwh * tariff_per_kwh

# --- GENERATE PESAN ALARM WHATSAPP ---
