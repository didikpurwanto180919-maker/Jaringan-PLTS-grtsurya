import time
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from datetime import datetime

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="PRO-BIFACIAL ML & Soiling Early Warning - PLTS 1.5 MWp",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ PRO-BIFACIAL ML: Performance Ratio Optimization & Soiling Early Warning")

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
    # Dataset riwayat simulasi 7 hari menunjukkan degradasi bertahap (soiling)
    history_data = {
        "Tanggal": [
            "2026-10-15", "2026-10-16", "2026-10-17", 
            "2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21"
        ],
        "POA_kWh_m2": [5.1, 2.3, 5.2, 5.0, 5.1, 4.9, 5.0],
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
st.sidebar.subheader("🎯 Nilai Acuan (Baseline)")
st.sidebar.markdown(f"**Baseline PR Saat Ini:** `{st.session_state.baseline_pr:.2f}%`")
NGROK_URL = st.sidebar.text_input(
    "🔗 Endpoint Mirror SCADA Ngrok", 
    value="https://reveler-striking-feminist.ngrok-free.dev"
)

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

# --- FORMULASI PERFORMANCE RATIO (PR) ---
# PR Standar
if poa_realtime > 0:
    p_expected_stc = installed_capacity * (poa_realtime / stc_irradiance)
    pr_actual = (p_total / p_expected_stc) * 100.0 if p_expected_stc > 0 else 0.0
    
    # PR Terkoreksi Suhu (IEC 61724 standard)
    temp_factor = 1.0 + gamma_pmax * (t_module - stc_temp)
    pr_temp_corrected = pr_actual / temp_factor if temp_factor != 0 else pr_actual
else:
    p_expected_stc = 0.0
    pr_actual = 0.0
    pr_temp_corrected = 0.0

pr_expected = 81.5  # Nilai ekspektasi PR teoritis kondisi operasional

# --- EVALUASI TREN SOILING & PERINGATAN (3 HARI BERTURUT-TURUT) ---
df_hist = st.session_state.historical_df.copy()
baseline = st.session_state.baseline_pr

# Hitung deviasi PR terhadap baseline
df_hist["Deviasi_PR"] = baseline - df_hist["PR_Terkoreksi"]
valid_days = df_hist[~df_hist["Anomali_Cuaca"]].tail(3)

# Logika pemicu peringatan
latest_drop = baseline - df_hist.iloc[-1]["PR_Terkoreksi"]
is_consecutive_drop_5_to_10 = len(valid_days) == 3 and (valid_days["Deviasi_PR"] >= (baseline * 0.05)).all()

if latest_drop >= (baseline * 0.10):
    alert_level = "CRITICAL"
    status_label = "Kritis (Pembersihan Segera Diperlukan)"
    status_color = "red"
elif is_consecutive_drop_5_to_10:
    alert_level = "WARNING"
    status_label = "Perlu Dijadwalkan Pembersihan"
    status_color = "orange"
else:
    alert_level = "NORMAL"
    status_label = "Modul Bersih / Beroperasi Optimal"
    status_color = "green"

# Estimasi Kehilangan Energi & Pendapatan Harian
# Energi rujukan insolasi harian tipikal ~5.0 PSH
daily_insol_kwh_m2 = 5.0
e_ideal_clean = installed_capacity * daily_insol_kwh_m2 * (baseline / 100.0)
e_actual_proj = installed_capacity * daily_insol_kwh_m2 * (df_hist.iloc[-1]["PR_Terkoreksi"] / 100.0)
daily_energy_loss_kwh = max(0.0, e_ideal_clean - e_actual_proj)
daily_revenue_loss_idr = daily_energy_loss_kwh * tariff_per_kwh

# --- PANEL METRIK KPI UTAMA ---
st.markdown("### 📊 Panel KPI Operasional PLTS")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric("PR Aktual", f"{pr_actual:.2f}%", delta=f"{pr_actual - pr_expected:.1f}% vs Target")
kpi2.metric("PR Terkoreksi Suhu", f"{pr_temp_corrected:.2f}%")
kpi3.metric("PR Ekspektasi", f"{pr_expected:.2f}%")
kpi4.metric("Daya Aktif Total", f"{p_total:,.2f} kW")
kpi5.metric("Status Kebersihan Modul", status_label)

st.markdown("---")

# --- WIDGET REKOMENDASI PEMBERSIHAN (CLEANING ACTION WIDGET) ---
st.markdown("### 🧹 Sistem Peringatan Pembersihan & Optimasi Finansial")

if alert_level == "CRITICAL":
    st.error(
        f"🚨 **LEVEL KRITIS:** PR modul turun lebih dari 10% dari baseline ({latest_drop:.2f}% deviasi) "
        "selama beberapa periode operasional cerah. Penumpukan *soiling* memerlukan tindakan segera."
    )
elif alert_level == "WARNING":
    st.warning(
        f"⚠️ **LEVEL PERINGATAN:** Terdeteksi penurunan PR bertahap 5%–10% dari baseline "
        "selama 3 hari berturut-turut tanpa anomali cuaca. Modul mulai tertutup debu."
    )
else:
    st.success("✅ **LEVEL NORMAL:** Performa modul optimal. Tidak ada akumulasi *soiling* signifikan.")

# Ringkasan dampak finansial
c_loss1, c_loss2, c_act1, c_act2 = st.columns([1.5, 1.5, 1, 1])

with c_loss1:
    st.metric(
        "Estimasi Kehilangan Energi", 
        f"{daily_energy_loss_kwh:,.1f} kWh/hari",
        delta=f"-{daily_energy_loss_kwh / e_ideal_clean * 100:.1f}%" if e_ideal_clean > 0 else "0%"
    )

with c_loss2:
    st.metric(
        "Estimasi Kehilangan Pendapatan", 
        f"Rp {daily_revenue_loss_idr:,.0f} / hari",
        delta=f"Rp {daily_revenue_loss_idr * 30:,.0f} / bln",
        delta_color="inverse"
    )

with c_act1:
    st.write("")
    if st.button("📅 Jadwalkan Pembersihan", use_container_width=True):
        st.session_state.cleaning_scheduled = True
        st.toast("Jadwal pembersihan berhasil dimasukkan ke sistem log maintenance!", icon="📝")

with c_act2:
    st.write("")
    if st.button("✨ Pembersihan Selesai (Reset)", use_container_width=True):
        # Reset baseline ke nilai terbaru setelah pembersihan
        st.session_state.baseline_pr = df_hist.iloc[0]["PR_Terkoreksi"]
        st.session_state.cleaning_scheduled = False
        st.toast("Baseline PR berhasil di-reset ke status modul bersih!", icon="✅")

if st.session_state.cleaning_scheduled:
    st.info("ℹ️ Status: Pembersihan modul sedang dalam antrean tim O&M lapangan.")

st.markdown("---")

# --- GRAFIK INTERAKTIF TREN HARIAN (PR VS RADIASI MATAHARI) ---
st.markdown("### 📈 Tren Harian Performance Ratio vs Iradiasi (Deteksi Soiling)")

fig = go.Figure()

# Garis PR Terkoreksi Suhu
fig.add_trace(go.Scatter(
    x=df_hist["Tanggal"], 
    y=df_hist["PR_Terkoreksi"],
    mode="lines+markers",
    name="PR Terkoreksi Suhu (%)",
    line=dict(color="#1e88e5", width=3),
    yaxis="y1"
))

# Garis Ambang Batas Baseline
fig.add_trace(go.Scatter(
    x=df_hist["Tanggal"],
    y=[st.session_state.baseline_pr] * len(df_hist),
    mode="lines",
    name=f"Baseline PR ({st.session_state.baseline_pr:.1f}%)",
    line=dict(color="#43a047", dash="dash"),
    yaxis="y1"
))

# Garis Ambang Batas Kritis (-10%)
fig.add_trace(go.Scatter(
    x=df_hist["Tanggal"],
    y=[st.session_state.baseline_pr * 0.90] * len(df_hist),
    mode="lines",
    name="Batas Kritis Pembersihan (-10%)",
    line=dict(color="#e53935", dash="dot"),
    yaxis="y1"
))

# Bar Chart Iradiasi Harian
fig.add_trace(go.Bar(
    x=df_hist["Tanggal"],
    y=df_hist["POA_kWh_m2"],
    name="Insolasi Harian (kWh/m²)",
    marker_color="rgba(255, 179, 0, 0.4)",
    yaxis="y2"
))

fig.update_layout(
    xaxis=dict(title="Tanggal"),
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
    height=400
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
