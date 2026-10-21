import time
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from datetime import datetime

# Import pustaka Machine Learning dengan fallback otomatis
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

# --- INISIALISASI SESSION STATE UNTUK RIWAYAT DAN BASELINE ---
BASELINE_DEFAULT = 82.5  # %

if "baseline_pr" not in st.session_state:
    st.session_state.baseline_pr = BASELINE_DEFAULT

if "cleaning_scheduled" not in st.session_state:
    st.session_state.cleaning_scheduled = False

if "historical_df" not in st.session_state:
    # Dataset riwayat 7 hari operasional (simulasi soiling bertahap)
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

# --- SIDEBAR KONFIGURASI SISTEM ---
st.sidebar.header("⚙️ Konfigurasi Sistem PLTS")
installed_capacity = st.sidebar.number_input("Kapasitas Terpasang (kWp)", value=1500.0, step=50.0)
stc_irradiance = 1000.0  # W/m²
gamma_pmax = st.sidebar.number_input("Koefisien Suhu Pmax (%/°C)", value=-0.38, step=0.01) / 100.0
stc_temp = 25.0  # °C
tariff_per_kwh = st.sidebar.number_input("Tarif Listrik (IDR/kWh)", value=1445, step=50)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Machine Learning Parameters")
st.sidebar.info(f"Model Engine: **{ML_MODEL_TYPE}**")
st.sidebar.markdown(f"**Baseline PR Bersih:** `{st.session_state.baseline_pr:.2f}%`")
NGROK_URL = st.sidebar.text_input(
    "🔗 Endpoint Mirror SCADA Ngrok", 
    value="https://reveler-striking-feminist.ngrok-free.dev"
)

# --- ENGINE MACHINE LEARNING: BENCHMARK MODUL BERSIH ---
@st.cache_resource
def train_clean_benchmark_model():
    np.random.seed(42)
    poa_samples = np.random.uniform(2.5, 6.5, 150)
    temp_samples = 25.0 + (poa_samples * 4.4) + np.random.normal(0, 1.2, 150)
    
    # Formula referensi fisik modul bersih pada kondisi optimal
    pr_clean_ideal = 82.5 - (0.0038 * (temp_samples - 25.0) * 8.0) + np.random.normal(0, 0.35, 150)
    
    X_synth = np.column_stack((poa_samples, temp_samples))
    y_synth = pr_clean_ideal
    
    if ML_MODEL_TYPE == "XGBoost Regressor":
        model = XGBRegressor(n_estimators=60, max_depth=3, learning_rate=0.08, random_state=42)
    else:
        model = XGBRegressor(n_estimators=60, max_depth=3, random_state=42)
        
    model.fit(X_synth, y_synth)
    return model

ml_clean_model = train_clean_benchmark_model()

# --- ENGINE AKUISISI TELEMETRI REAL-TIME ---
def get_current_telemetry():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
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

# --- INFERENSI ML & PROYEKSI LAJU DEBU (SOILING DRIFT) ---
df_hist = st.session_state.historical_df.copy()

# 1. Prediksi PR Bersih oleh XGBoost
X_eval = df_hist[["POA_kWh_m2", "Suhu_Modul_C"]].values
df_hist["ML_Predicted_Clean_PR"] = ml_clean_model.predict(X_eval)

# 2. Isolasi Soiling Index (Residual)
df_hist["Soiling_Loss_Pct"] = np.maximum(0.0, df_hist["ML_Predicted_Clean_PR"] - df_hist["PR_Terkoreksi"])

# 3. Regresi Tren Laju Penurunan pada Hari Normal (Clear Sky)
clean_weather_days = df_hist[~df_hist["Anomali_Cuaca"]]
reg = LinearRegression()
reg.fit(clean_weather_days[["Hari_Ke"]], clean_weather_days["PR_Terkoreksi"])
daily_soiling_rate = -float(reg.coef_[0])  # % penurunan per hari

# 4. Proyeksi Hari Menuju Batas Kritis (-10% Baseline)
critical_threshold = st.session_state.baseline_pr * 0.90
latest_pr = df_hist.iloc[-1]["PR_Terkoreksi"]
latest_clean_benchmark = df_hist.iloc[-1]["ML_Predicted_Clean_PR"]
current_soiling_loss = df_hist.iloc[-1]["Soiling_Loss_Pct"]

if daily_soiling_rate > 0.01:
    days_to_critical = int(np.ceil((latest_pr - critical_threshold) / daily_soiling_rate))
    days_to_critical = max(0, days_to_critical)
else:
    days_to_critical = 99

# Proyeksi 3 Hari ke Depan
future_days = np.array([[8], [9], [10]])
future_pr_forecast = reg.predict(future_days)

# --- PENENTUAN STATUS & ALERT LOGIC ---
if latest_pr <= critical_threshold:
    alert_level = "CRITICAL"
    status_label = "Kritis (Pembersihan Diperlukan)"
elif current_soiling_loss >= (st.session_state.baseline_pr * 0.05):
    alert_level = "WARNING"
    status_label = "Perlu Dijadwalkan Pembersihan"
else:
    alert_level = "NORMAL"
    status_label = "Modul Bersih / Beroperasi Optimal"

# Estimasi Kehilangan Energi & Pendapatan Harian
daily_insol_kwh_m2 = 5.0
e_ideal_clean = installed_capacity * daily_insol_kwh_m2 * (latest_clean_benchmark / 100.0)
e_actual_proj = installed_capacity * daily_insol_kwh_m2 * (latest_pr / 100.0)
daily_energy_loss_kwh = max(0.0, e_ideal_clean - e_actual_proj)
daily_revenue_loss_idr = daily_energy_loss_kwh * tariff_per_kwh

# --- PANEL METRIK KPI UTAMA ---
st.markdown("### 📊 Panel KPI Operasional & Machine Learning Insights")
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("PR Terkoreksi Aktual", f"{latest_pr:.2f}%", delta=f"-{current_soiling_loss:.2f}% (Soiling)", delta_color="inverse")
k2.metric("ML Expected Clean PR", f"{latest_clean_benchmark:.2f}%")
k3.metric("Laju Soiling Harian", f"{daily_soiling_rate:.2f}% / hari")
k4.metric("Proyeksi Batas Kritis", f"{days_to_critical} Hari Lagi" if alert_level != "CRITICAL" else "Tercapai!")
k5.metric("Status AI Diagnostic", status_label)

st.markdown("---")

# --- WIDGET REKOMENDASI PEMBERSIHAN ---
st.markdown("### 🧹 Sistem Peringatan Pembersihan & Estimasi Finansial")

if alert_level == "CRITICAL":
    st.error(
        f"🚨 **LEVEL KRITIS:** PR aktual ({latest_pr:.2f}%) telah menembus batas toleransi kritis (-10% dari baseline). "
        f"Estimasi kerugian produksi mencapai **{daily_energy_loss_kwh:,.1f} kWh/hari** akibat penumpukan debu."
    )
elif alert_level == "WARNING":
    st.warning(
        f"⚠️ **LEVEL PERINGATAN:** AI mendeteksi akumulasi debu konsisten dengan laju **{daily_soiling_rate:.2f}% per hari**. "
        f"Diproyeksikan menyentuh level kritis dalam **{days_to_critical} hari** jika tidak dibersihkan."
    )
else:
    st.success("✅ **LEVEL NORMAL:** Performa modul beroperasi optimal dalam batas toleransi model ML.")

c_loss1, c_loss2, c_act1, c_act2 = st.columns([1.5, 1.5, 1.2, 1.2])

with c_loss1:
    st.metric(
        "Kehilangan Energi (Loss kWh)", 
        f"{daily_energy_loss_kwh:,.1f} kWh/hari",
        delta=f"-{daily_energy_loss_kwh / e_ideal_clean * 100:.1f}% Potensi" if e_ideal_clean > 0 else "0%"
    )

with c_loss2:
    st.metric(
        "Kehilangan Pendapatan", 
        f"Rp {daily_revenue_loss_idr:,.0f} / hari",
        delta=f"Rp {daily_revenue_loss_idr * 30:,.0f} / bulan",
        delta_color="inverse"
    )

with c_act1:
    st.write("")
    if st.button("📅 Jadwalkan Pembersihan", use_container_width=True):
        st.session_state.cleaning_scheduled = True
        st.toast("Work order pembersihan diteruskan ke tim O&M!", icon="📝")

with c_act2:
    st.write("")
    if st.button("✨ Pembersihan Selesai (Reset)", use_container_width=True):
        st.session_state.baseline_pr = df_hist.iloc[0]["PR_Terkoreksi"]
        st.session_state.cleaning_scheduled = False
        st.toast("Baseline PR dan calibration engine berhasil di-reset!", icon="✅")

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
trend_y = [latest_pr] + list(future_pr_forecast)

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

st.markdown("---")

# --- MONITORING DETAIL INVERTER 01 - 12 ---
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
                st.caption("🟢 Status: Normal")

st.markdown("---")

# Embedding Live Mirror SCADA
st.subheader("🖥️ Live Mirror SCADA PLTS")
try:
    st.components.v1.iframe(NGROK_URL, height=600, scrolling=True)
except Exception as e:
    st.error(f"Gagal memuat iframe SCADA: {e}")

time.sleep(5)
st.rerun()
