import time
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from datetime import datetime

# Machine Learning Libraries
from sklearn.linear_model import LinearRegression
try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    from sklearn.ensemble import RandomForestRegressor
    HAS_XGB = False

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="PRO-BIFACIAL ML: Smart Soiling Early Warning PLTS 1.5 MWp",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ PRO-BIFACIAL ML: Performance Ratio Optimization & AI Soiling Detection")

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

# --- INISIALISASI SESSION STATE & DATASET TELEMETRI RIWAYAT ---
BASELINE_DEFAULT = 82.5  # %

if "baseline_pr" not in st.session_state:
    st.session_state.baseline_pr = BASELINE_DEFAULT

if "cleaning_scheduled" not in st.session_state:
    st.session_state.cleaning_scheduled = False

if "historical_df" not in st.session_state:
    # Data riwayat 7 hari operasional
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
        "Anomali_Cuaca": [False, True, False, False, False, False, False]
    }
    st.session_state.historical_df = pd.DataFrame(history_data)

# --- SIDEBAR KONFIGURASI SISTEM ---
st.sidebar.header("⚙️ Konfigurasi Sistem PLTS")
installed_capacity = st.sidebar.number_input("Kapasitas Terpasang (kWp)", value=1500.0, step=50.0)
stc_irradiance = 1000.0  # W/m²
gamma_pmax = st.sidebar.number_input("Koefisien Suhu Pmax (%/°C)", value=-0.38, step=0.01) / 100.0
stc_temp = 25.0
tariff_per_kwh = st.sidebar.number_input("Tarif Listrik (IDR/kWh)", value=1445, step=50)

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Engine Machine Learning")
st.sidebar.info(f"Model: **{'XGBoost Regressor' if HAS_XGB else 'Random Forest Regressor'}** + Soiling Trend Projection")
st.sidebar.markdown(f"**Baseline PR Bersih:** `{st.session_state.baseline_pr:.2f}%`")
NGROK_URL = st.sidebar.text_input(
    "🔗 Endpoint Mirror SCADA Ngrok", 
    value="https://reveler-striking-feminist.ngrok-free.dev"
)

# --- ENGINE MACHINE LEARNING UNTUK PREDIKSI PR BERSIH & PROYEKSI SOILING ---
@st.cache_resource
def train_clean_baseline_model():
    # Training data sintetis kondisi modul bersih (Clean State Reference)
    np.random.seed(42)
    poa_samples = np.random.uniform(2.0, 6.5, 120)
    temp_samples = 25.0 + (poa_samples * 4.5) + np.random.normal(0, 1.5, 120)
    
    # Model ideal PR bersih berada di sekitar 82.5% dengan fluktuasi mikro suhu
    pr_clean_target = 82.5 - (0.0038 * (temp_samples - 25.0) * 10.0) + np.random.normal(0, 0.4, 120)
    
    X_train = np.column_stack((poa_samples, temp_samples))
    y_train = pr_clean_target
    
    if HAS_XGB:
        model = XGBRegressor(n_estimators=60, max_depth=3, learning_rate=0.08, random_state=42)
    else:
        model = RandomForestRegressor(n_estimators=60, max_depth=3, random_state=42)
        
    model.fit(X_train, y_train)
    return model

ml_model = train_clean_baseline_model()

# Evaluasi Data Riwayat dengan ML
df_hist = st.session_state.historical_df.copy()
X_eval = df_hist[["POA_kWh_m2", "Suhu_Modul_C"]].values
df_hist["ML_Predicted_Clean_PR"] = ml_model.predict(X_eval)

# Soiling Ratio / Soiling Loss = ML Clean PR - Actual PR Terkoreksi
df_hist["Soiling_Loss_Pct"] = np.maximum(0.0, df_hist["ML_Predicted_Clean_PR"] - df_hist["PR_Terkoreksi"])

# Regresi Tren Soiling Harian pada hari cerah (Clear-Sky Days Only)
clean_weather_days = df_hist[~df_hist["Anomali_Cuaca"]]
reg = LinearRegression()
reg.fit(clean_weather_days[["Hari_Ke"]], clean_weather_days["PR_Terkoreksi"])
daily_soiling_rate = -float(reg.coef_[0])  # Laju penurunan % per hari

# Prediksi Proyeksi 3 Hari ke Depan (Forecasting)
future_days = np.array([[8], [9], [10]])
future_pr_preds = reg.predict(future_days)
days_until_critical = max(0, int(np.ceil((clean_weather_days["PR_Terkoreksi"].iloc[-1] - (st.session_state.baseline_pr * 0.90)) / daily_soiling_rate))) if daily_soiling_rate > 0 else 99

# --- STATUS DAN ALERT LOGIC ---
current_soiling_loss = df_hist.iloc[-1]["Soiling_Loss_Pct"]
latest_pr = df_hist.iloc[-1]["PR_Terkoreksi"]
critical_threshold = st.session_state.baseline_pr * 0.90

if latest_pr <= critical_threshold:
    alert_level = "CRITICAL"
    status_label = "Kritis (Pembersihan Segera Diperlukan)"
    status_color = "red"
elif current_soiling_loss >= (st.session_state.baseline_pr * 0.05):
    alert_level = "WARNING"
    status_label = "Perlu Dijadwalkan Pembersihan"
    status_color = "orange"
else:
    alert_level = "NORMAL"
    status_label = "Modul Bersih / Beroperasi Optimal"
    status_color = "green"

# Kalkulasi Kehilangan Energi & Kerugian Finansial Harian
daily_insol_kwh_m2 = 5.0
e_clean_expected = installed_capacity * daily_insol_kwh_m2 * (df_hist.iloc[-1]["ML_Predicted_Clean_PR"] / 100.0)
e_actual_achieved = installed_capacity * daily_insol_kwh_m2 * (latest_pr / 100.0)
daily_energy_loss_kwh = max(0.0, e_clean_expected - e_actual_achieved)
daily_revenue_loss_idr = daily_energy_loss_kwh * tariff_per_kwh

# --- PANEL METRIK UTAMA ---
st.markdown("### 📊 Indikator Kinerja & Machine Learning Insights")
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("PR Terkoreksi Aktual", f"{latest_pr:.2f}%", delta=f"-{current_soiling_loss:.2f}% (Soiling)", delta_color="inverse")
k2.metric("ML Expected Clean PR", f"{df_hist.iloc[-1]['ML_Predicted_Clean_PR']:.2f}%")
k3.metric("Laju Soiling Harian", f"{daily_soiling_rate:.2f}% / hari")
k4.metric("Proyeksi Batas Kritis", f"{days_until_critical} Hari Lagi" if alert_level != "CRITICAL" else "Telah Tercapai!")
k5.metric("Status AI Diagnostic", status_label)

st.markdown("---")

# --- WIDGET REKOMENDASI PEMBERSIHAN ---
st.markdown("### 🧹 Sistem Peringatan Pembersihan & Estimasi Finansial")

if alert_level == "CRITICAL":
    st.error(
        f"🚨 **LEVEL KRITIS:** PR aktual ({latest_pr:.2f}%) telah menembus batas toleransi kritis (-10% dari baseline). "
        f"Estimasi kerugian produksi harian mencapai **{daily_energy_loss_kwh:,.1f} kWh**."
    )
elif alert_level == "WARNING":
    st.warning(
        f"⚠️ **LEVEL PERINGATAN:** AI mendeteksi akumulasi debu dengan laju **{daily_soiling_rate:.2f}% per hari**. "
        f"Diproyeksikan mencapai level kritis dalam **{days_until_critical} hari** jika tidak dibersihkan."
    )
else:
    st.success("✅ **LEVEL NORMAL:** Performa modul optimal. Tidak ada akumulasi soiling yang melebihi batas batas ambang toleransi.")

c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.2, 1.2])

with c1:
    st.metric(
        "Kehilangan Energi (Loss kWh)", 
        f"{daily_energy_loss_kwh:,.1f} kWh/hari",
        delta=f"-{daily_energy_loss_kwh / e_clean_expected * 100:.1f}% Potensi" if e_clean_expected > 0 else "0%"
    )

with c2:
    st.metric(
        "Kehilangan Pendapatan", 
        f"Rp {daily_revenue_loss_idr:,.0f} / hari",
        delta=f"Rp {daily_revenue_loss_idr * 30:,.0f} / bulan",
        delta_color="inverse"
    )

with c3:
    st.write("")
    if st.button("📅 Jadwalkan Pembersihan", use_container_width=True):
        st.session_state.cleaning_scheduled = True
        st.toast("Work order pembersihan modul diteruskan ke tim O&M!", icon="📋")

with c4:
    st.write("")
    if st.button("✨ Pembersihan Selesai (Reset)", use_container_width=True):
        st.session_state.baseline_pr = df_hist.iloc[0]["PR_Terkoreksi"]
        st.session_state.cleaning_scheduled = False
        st.toast("Baseline PR dan model calibration berhasil di-reset!", icon="✅")

if st.session_state.cleaning_scheduled:
    st.info("ℹ️ Status: Pembersihan modul sedang berlangsung atau masuk dalam antrean maintenance.")

st.markdown("---")

# --- GRAFIK INTERAKTIF TREN HARIAN & PREDIKSI ML ---
st.markdown("### 📈 Tren Harian Performance Ratio vs Iradiasi & Proyeksi AI (Soiling Drift)")

fig = go.Figure()

# 1. Bar Chart Iradiasi Harian
fig.add_trace(go.Bar(
    x=df_hist["Tanggal"],
    y=df_hist["POA_kWh_m2"],
    name="POA Insolasi Harian (kWh/m²)",
    marker_color="rgba(255, 183, 77, 0.45)",
    yaxis="y2"
))

# 2. Garis PR Terkoreksi Suhu (Aktual Terukur)
fig.add_trace(go.Scatter(
    x=df_hist["Tanggal"], 
    y=df_hist["PR_Terkoreksi"],
    mode="lines+markers",
    name="PR Terkoreksi Suhu (%)",
    line=dict(color="#1976d2", width=3),
    yaxis="y1"
))

# 3. Garis Model ML: Ekspektasi Modul Bersih (Clean Benchmark)
fig.add_trace(go.Scatter(
    x=df_hist["Tanggal"],
    y=df_hist["ML_Predicted_Clean_PR"],
    mode="lines",
    name="ML Predicted Clean PR (%)",
    line=dict(color="#00897b", dash="dash", width=2),
    yaxis="y1"
))

# 4. Garis Ambang Batas Baseline Tetap
fig.add_trace(go.Scatter(
    x=df_hist["Tanggal"],
    y=[st.session_state.baseline_pr] * len(df_hist),
    mode="lines",
    name=f"Baseline PR ({st.session_state.baseline_pr:.1f}%)",
    line=dict(color="#43a047", dash="dot"),
    yaxis="y1"
))

# 5. Garis Ambang Batas Kritis (-10%)
fig.add_trace(go.Scatter(
    x=df_hist["Tanggal"],
    y=[critical_threshold] * len(df_hist),
    mode="lines",
    name="Batas Kritis Pembersihan (-10%)",
    line=dict(color="#e53935", dash="dot", width=2),
    yaxis="y1"
))

# 6. Proyeksi Tren Soiling (Forward Regression Line)
future_dates = ["2026-10-22", "2026-10-23", "2026-10-24"]
trend_x = list(df_hist["Tanggal"].iloc[-1:]) + future_dates
trend_y = [df_hist["PR_Terkoreksi"].iloc[-1]] + list(future_pr_preds)

fig.add_trace(go.Scatter(
    x=trend_x,
    y=trend_y,
    mode="lines+markers",
    name="Proyeksi Penurunan AI (Forecast)",
    line=dict(color="#ab47bc", dash="dashdot", width=2),
    yaxis="y1"
))

fig.update_layout(
    xaxis=dict(title="Tanggal Operasional"),
    yaxis=dict(title="Performance Ratio (%)", range=[60, 95], side="left"),
    yaxis2=dict(
        title="POA Insolasi (kWh/m²)",
        overlaying="y",
        side="right",
        range=[0, 7],
        showgrid=False
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    margin=dict(l=40, r=40, t=30, b=40),
    height=440
)

st.plotly_chart(fig, use_container_width=True)

# Auto-refresh loop
time.sleep(5)
st.rerun()
