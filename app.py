import streamlit as st

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard PLTS GRT Surya",
    page_icon="⚡",
    layout="wide",
)

# Judul Aplikasi
st.title("⚡ Dashboard Monitoring GRT Surya - PLTS")
st.markdown("---")

# Sidebar untuk konfigurasi URL Ngrok
st.sidebar.header("⚙️ Konfigurasi Koneksi")
st.sidebar.info(
    "Masukkan URL publik Ngrok yang aktif dari server internal pembangkit."
)

# Input URL Ngrok oleh pengguna (bisa diubah dinamis atau di-hardcode)
ngrok_url = st.sidebar.text_input(
    "URL Ngrok (contoh: https://xxxx.ngrok-free.app)",
    value="",  # Masukkan URL ngrok default Anda di sini jika ada
)

# Main Content
if not ngrok_url:
    st.warning(
        "⚠️ Silakan masukkan **URL Ngrok** yang valid pada sidebar sebelah kiri untuk mulai melakukan mirror."
    )

    with st.expander("📖 Panduan Singkat"):
        st.markdown(
            """
        1. Pastikan komputer lokal di jaringan internal PLTS sudah menjalankan perintah Ngrok:
           ```bash
           ngrok http [http://grtsurya.indonesiapower.co.id:82](http://grtsurya.indonesiapower.co.id:82)
           ```
        2. Salin URL HTTPS yang dihasilkan oleh Ngrok (contoh: `https://xxxx.ngrok-free.app`).
        3. Masukkan URL tersebut ke kolom input di sidebar aplikasi ini.
        """
        )
else:
    # Perbaikan Syntax: Tambahkan tanda f-string yang benar di sini
    st.success(f"Menampilkan mirror dari server internal via: `{ngrok_url}`")

    # Embedding halaman web internal menggunakan iframe Streamlit
    try:
        st.components.v1.iframe(ngrok_url, height=800, scrolling=True)
    except Exception as e:
        st.error(
            f"Gagal memuat iframe. Periksa apakah URL Ngrok masih aktif. Error: {e}"
        )
