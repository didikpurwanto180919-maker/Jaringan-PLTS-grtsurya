import time
import urllib.parse
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from datetime import datetime

# Import Scikit-Learn / XGBoost
from sklearn.linear_model import LinearRegression
try:
    from xgboost import XGBRegressor
    ML_MODEL_TYPE = "XGBoost Regressor"
except ImportError:
    from sklearn.ensemble import RandomForestRegressor as XGBRegressor
    ML_MODEL_TYPE = "RandomForest (Fallback)"

# --- KONFIGURASI HALAMAN STREAMLIT ---
st.set_page_config(
    page_title="PRO-BIFACIAL ML & Soiling Early Warning - PLTS 1.5 MWp",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ PRO-BIFACIAL ML: Performance Ratio Optimization & AI Soiling Early Warning")

# --- WIDGET JAM REAL-TIME ---
clock_html = """
<div style="font-family: monospace; font-size: 15px; font-weight: bold; color: #1b5e20; background-color: #e8f5e9; padding: 6px 12px; border-radius: 6px; display: inline-block;">
    📅 Waktu Sistem (WIB): <span id="live-clock"></span>
</div>
<script>
function updateClock() {
    const now = new Date();
    const options = { timeZone: 'Asia/Jakarta', weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false };
    document.getElementById('live-clock').innerText = now.toLocaleString('id-ID', options);
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

if "historical_df" not in st.session_state:
    history_data = {
        "Hari_Ke": [1, 2, 3, 4, 5, 6, 7],
        "Tanggal": [
            "2026-10-16", "2026-10-17", "2026-10-18", 
            "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22"
        ],
        "POA_kWh_m2": [5.1, 2.3, 5.2, 5.0, 5.1, 4.9, 5.0],
        "Suhu_Modul_C": [47.5, 31.0, 48.2, 47.0, 48.0, 46.8, 47.2],
        "Actual_PR": [82.1, 79.2, 77.4, 75.8, 74.0, 72.3, 71.1],
        "PR_Terkoreksi": [82.4, 80.1, 77.9, 76.1, 74.3, 72.8, 71.5],
        "Cuaca": ["Cerah", "Hujan/Mendung", "Cerah", "Cerah", "Cerah", "Cerah", "Cerah"],
        "Anomali_Cuaca": [False, True, False, False, False, False, False]
    }
    st.session_state.historical_df = pd.DataFrame(history_data)

# --- SIDEBAR KONFIGURASI SISTEM ---
st.sidebar.header("⚙️ Konfigurasi Sistem PLTS")
installed_capacity = st.sidebar.number_input("Kapasitas Terpasang (kWp)", value=1500.0, step=50.0)
stc_irradiance = 1000.0  # W/m²
gamma_pmax = st.sidebar.number_input("Koefisien Suhu Pmax (%/°C)", value=-0.38, step=0.01) / 100.0
stc_temp = 25.0  # °C
tilt_angle = st.sidebar.slider("Sudut Kemiringan (Tilt Angle)", value=10.0, min_value=0.0, max_value=45.0, step=1.0)
soil_albedo = st.sidebar.number_input("Albedo Tanah (Soil Albedo)", value=0.08, step=0.01)
tariff_per_kwh = st.sidebar.number_input("Tarif Listrik (IDR/kWh)", value=1445, step=50)

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Konfigurasi Alarm WhatsApp")
wa_phone_number = st.sidebar.text_input(
    "Nomor WhatsApp Tujuan",
    value="6281234567890",
    help="Nomor tujuan untuk pengiriman alert via WhatsApp Web"
)

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Engine Machine Learning")
st.sidebar.info(f"Model Engine: **{ML_MODEL_TYPE}**")
st.sidebar.markdown(f"**Baseline PR Bersih:** `{st.session_state.baseline_pr:.2f}%`")
NGROK_URL = st.sidebar.text_input(
    "🔗 Endpoint Mirror SCADA Ngrok", 
    value="https://reveler-striking-feminist.ngrok-free.dev"
)

# --- ENGINE MACHINE LEARNING: BENCHMARK MODUL BERSIH ---
@st.cache_resource
def get_clean_benchmark_model():
    np.random.seed(42)
    poa_samples = np.random.uniform(2.5, 6.5, 150)
    temp_samples = 25.0 + (poa_samples * 4.4) + np.random.normal(0, 1.2, 150)
    pr_clean_ideal = 82.5 - (0.0038 * (temp_samples - 25.0) * 8.0) + np.random.normal(0, 0.35, 150)
    
    X_synth = np.column_stack((poa_samples, temp_samples))
    y_synth = pr_clean_ideal
    
    if ML_MODEL_TYPE == "XGBoost Regressor":
        model = XGBRegressor(n_estimators=60, max_depth=3, learning_rate=0.08, random_state=42)
    else:
        model = XGBRegressor(n_estimators=60, max_depth=3, random_state=42)
        
    model.fit(X_synth, y_synth)
    return model

ml_clean_model = get_clean_benchmark_model()

# --- ENGINE AKUISISI TELEMETRI REAL-TIME (WIB Current Hour Constraint) ---
def get_current_telemetry():
    now_utc = datetime.utcnow()
    # Konversi ke WIB (UTC +7)
    hour = (now_utc.hour + 7) % 24
    minute = now_utc.minute
    micro = np.sin(minute * np.pi / 30) * 0.15

    if 6 <= hour <= 17:
        base_power = max(0.5, 3.5 - abs(hour - 12) * 0.4) + micro
        poa = max(50.0, 820.0 - abs(hour - 12) * 115.0)
    else:
        base_power = 0.0
        poa = 0.0

    t_mod = 31.0 + (np.sin(hour * np.pi / 24) * 18.0)
    total_power = 0.0
    inverters = []

    for i in range(1, 13):
        cap = 128.4 if i <= 11 else 87.6
        p = round(max(0.0, (base_power + (i * 0.02) if i <= 11 else base_power - 0.75)), 2)
        inverters.append({"id": i, "name": f"Inverter {i:02d}", "power": p, "capacity": cap})
        total_power += p

    return total_power, poa, t_mod, inverters

p_total, poa_realtime, t_module, inverters_list = get_current_telemetry()

# Formulasi PR Standar & PR Terkoreksi Suhu (IEC 61724)
if poa_realtime > 0:
    p_expected_stc = installed_capacity * (poa_realtime / stc_irradiance)
    pr_actual = (p_total / p_expected_stc) * 100.0 if p_expected_stc > 0 else 0.0
    temp_factor = 1.0 + gamma_pmax * (t_module - stc_temp)
    pr_temp_corrected = pr_actual / temp_factor if temp_factor != 0 else pr_actual
else:
    p_expected_stc = 0.0
    pr_actual = 0.0
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
    status_label = "Kritis (Pembersihan Segera Diperlukan)"
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

# --- PANEL METRIK UTAMA ---
st.markdown("### 📊 Indikator Kinerja & Machine Learning Insights")
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("PR Terkoreksi Aktual", f"{latest_pr:.2f}%", delta=f"-{current_soiling_loss:.2f}% (Soiling)", delta_color="inverse")
k2.metric("ML Expected Clean PR", f"{latest_clean_benchmark:.2f}%")
k3.metric("Laju Soiling Harian", f"{daily_soiling_rate:.2f}% / hari")
k4.metric("Proyeksi Batas Kritis", f"{days_to_critical} Hari Lagi" if alert_level != "CRITICAL" else "Tercapai!")
k5.metric("Status AI Diagnostic", status_label)

st.markdown("---")

# --- WIDGET REKOMENDASI PEMBERSIHAN & ALARM WHATSAPP ---
st.markdown("### 🧹 Sistem Peringatan Pembersihan & Integrasi Alarm WhatsApp")

if alert_level == "CRITICAL":
    st.error(f"🚨 **LEVEL KRITIS:** PR aktual ({latest_pr:.2f}%) menembus batas kritis toleransi (-10% dari baseline). Kehilangan energi mencapai **{daily_energy_loss_kwh:,.1f} kWh/hari**.")
elif alert_level == "WARNING":
    st.warning(f"⚠️ **LEVEL PERINGATAN:** Terdeteksi laju soiling **{daily_soiling_rate:.2f}% per hari**. Diproyeksikan mencapai level kritis dalam **{days_to_critical} hari**.")
else:
    st.success("✅ **LEVEL NORMAL:** Performa modul optimal di dalam koridor toleransi model ML.")

c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.2, 1.2])

with c1:
    st.metric("Kehilangan Energi (Loss kWh)", f"{daily_energy_loss_kwh:,.1f} kWh/hari")
with c2:
    st.metric("Kehilangan Pendapatan", f"Rp {daily_revenue_loss_idr:,.0f} / hari")
with c3:
    st.write("")
    if st.button("📅 Jadwalkan Pembersihan", use_container_width=True):
        st.session_state.cleaning_scheduled = True
        st.toast("Work order pembersihan modul dimasukkan ke jadwal O&M!", icon="📝")
with c4:
    st.write("")
    if st.button("✨ Pembersihan Selesai (Reset)", use_container_width=True):
        st.session_state.baseline_pr = df_hist.iloc[0]["PR_Terkoreksi"]
        st.session_state.cleaning_scheduled = False
        st.toast("Baseline PR dan calibration ML berhasil di-reset!", icon="✅")

# WhatsApp Web Link Generator
waktu_sekarang_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
wa_message_raw = (
    f"🚨 *[PERINGATAN DINI - PLTS 1.5 MWp]* 🚨\n\n"
    f"📅 *Waktu:* {waktu_sekarang_str} WIB\n"
    f"⚠️ *Status Alert:* {status_label}\n"
    f"📉 *PR Aktual Terkoreksi:* {latest_pr:.2f}%\n"
    f"🤖 *ML Clean Benchmark:* {latest_clean_benchmark:.2f}%\n"
    f"🍂 *Soiling Loss:* -{current_soiling_loss:.2f}%\n"
    f"📈 *Laju Soiling Harian:* {daily_soiling_rate:.2f}% / hari\n"
    f"⏳ *Proyeksi Batas Kritis:* {days_to_critical} hari lagi\n"
    f"⚡ *Potensi Energi Hilang:* {daily_energy_loss_kwh:,.1f} kWh/hari\n"
    f"💰 *Estimasi Kerugian:* Rp {daily_revenue_loss_idr:,.0f} / hari\n\n"
    f"📌 *Rekomendasi:* Segera laksanakan prosedur pencucian modul PV."
)
encoded_wa_text = urllib.parse.quote(wa_message_raw)
wa_web_url = f"https://web.whatsapp.com/send?phone={wa_phone_number}&text={encoded_wa_text}"

st.markdown("#### 📲 Eksekusi Alarm Cepat ke WhatsApp")
st.link_button(f"📲 Buka WhatsApp Web & Kirim Alarm ({alert_level})", url=wa_web_url, type="primary" if alert_level in ["CRITICAL", "WARNING"] else "secondary")

st.markdown("---")

# --- MONITORING DETAIL INVERTER 01 - 12 (SESUAI GAMBAR SCADA) ---
st.markdown("### 🔌 Telemetri Inverter Modular (Inverter 01 - 12)")

cols_per_row = 4
rows = [inverters_list[i:i + cols_per_row] for i in range(0, len(inverters_list), cols_per_row)]

for row in rows:
    cols = st.columns(len(row))
    for idx, inv in enumerate(row):
        with cols[idx]:
            inv_name = inv.get("name", f"Inverter {idx+1:02d}")
            inv_power = float(inv.get("power", 0.0))
            inv_cap = float(inv.get("capacity", 128.4))

            if poa_realtime > 0:
                inv_expected_p = inv_cap * (poa_realtime / stc_irradiance)
                inv_pr = (inv_power / inv_expected_p) * 100.0 if inv_expected_p > 0 else 0.0
            else:
                inv_pr = 0.0

            with st.container(border=True):
                st.markdown(f"**{inv_name}**")
                st.caption(f"Kapasitas: {inv_cap:.1f} kWp")
                st.metric("Output Daya", f"{inv_power:.2f} kW")
                st.metric("PR Inverter", f"{inv_pr:.2f}%")
                st.markdown("🟢 Status: Normal")

st.markdown("---")

# Embedding Live Mirror SCADA
st.subheader("🖥️ Live Mirror SCADA PLTS")
try:
    st.components.v1.iframe(NGROK_URL, height=600, scrolling=True)
except Exception as e:
    st.error(f"Gagal memuat iframe SCADA: {e}")

time.sleep(5)
st.rerun()
