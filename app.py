import streamlit as st
import pandas as pd
from datetime import datetime
from google_sheets import connect_to_gsheet, load_sheet, save_sheet

# --- Koneksi ke Google Spreadsheet ---
sheet_gsheet = connect_to_gsheet("Data Kas Gang")
sheet_warga = sheet_gsheet.worksheet("Warga")
sheet_iuran = sheet_gsheet.worksheet("Iuran")
sheet_pengeluaran = sheet_gsheet.worksheet("Pengeluaran")

# --- Load data dari Google Sheets ---
df_warga = load_sheet(sheet_warga)
df_iuran = load_sheet(sheet_iuran)
df_keluar = load_sheet(sheet_pengeluaran)

# --- Sidebar login info ---
if 'login' not in st.session_state:
    st.session_state.login = False
    st.session_state.username = ''
    st.session_state.role = ''

if not st.session_state.login:
    st.set_page_config(page_title="Iuran Kas RT", layout="wide")
    st.markdown("""
        <style>
        body { background-color: #111827; }
        .stApp { background-color: #111827; color: white; }
        .login-container { margin-top: 100px; text-align: center; }
        .login-box {
            background-color: #1f2937;
            padding: 40px;
            border-radius: 15px;
            width: 100%;
            max-width: 400px;
            margin: auto;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        }
        </style>
        <div class="login-container">
            <div class="login-box">
                <h1 style='color:white;'><span style='font-size: 1.5em;'>🔐</span> Login Iuran Kas RT</h1>
    """, unsafe_allow_html=True)

    users = {
        "admin": {"password": "admin123", "role": "admin"},
        "warga1": {"password": "warga123", "role": "warga"},
        "warga2": {"password": "warga123", "role": "warga"},
    }

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_clicked = st.button("Login")

    if login_clicked:
        if username in users and password == users[username]['password']:
            st.session_state.login = True
            st.session_state.username = username
            st.session_state.role = users[username]['role']
            st.rerun()
        else:
            st.error("Username atau password salah.")

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

role = st.session_state.role
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Tambah Iuran", "Tambah Pengeluaran", "Laporan Status Iuran"] if role == "admin" else ["Dashboard", "Laporan Status Iuran"])

if menu == "Laporan Status Iuran":
    st.title("📝 Laporan Status Iuran")
    df_iuran["Tanggal"] = pd.to_datetime(df_iuran["Tanggal"], errors='coerce')
    df_iuran["Bulan"] = df_iuran["Tanggal"].dt.to_period("M")

    bulan_terakhir = df_iuran["Bulan"].max()
    laporan = []

    for _, row in df_warga.iterrows():
        warga = row["Nama"]
        pembayaran = df_iuran[(df_iuran["Nama"] == warga) & (df_iuran["Bulan"] == bulan_terakhir)]
        status = "Lunas" if not pembayaran.empty else "Belum Lunas"
        laporan.append({"Nama": warga, "Bulan": str(bulan_terakhir), "Status": status})

    df_laporan = pd.DataFrame(laporan)
    st.dataframe(df_laporan, use_container_width=True)

if menu == "Tambah Iuran" and role == "admin":
    st.title("➕ Tambah Iuran")
    nama = st.selectbox("Nama Warga", df_warga["Nama"])
    tanggal = st.date_input("Tanggal", datetime.today())
    kategori = st.selectbox("Kategori Iuran", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang", "Lain-lain"])

    if kategori == "Iuran Pokok":
        jumlah_default = 35000
    elif kategori == "Iuran Kas Gang":
        jumlah_default = 15000
    elif kategori == "Iuran Pokok+Kas Gang":
        jumlah_default = 50000
    else:
        jumlah_default = 0

    jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000, value=jumlah_default)

    if st.button("Simpan Iuran"):
        new_id = int(df_iuran["ID"].max()) + 1 if not df_iuran.empty else 1
        new_row = {
            "ID": new_id,
            "Nama": nama,
            "Tanggal": tanggal.strftime("%Y-%m-%d"),
            "Jumlah": jumlah,
            "Kategori": kategori
        }
        df_iuran = pd.concat([df_iuran, pd.DataFrame([new_row])], ignore_index=True)
        save_sheet(sheet_iuran, df_iuran)
        st.success("✅ Data iuran berhasil disimpan!")

if menu == "Tambah Pengeluaran" and role == "admin":
    st.title("➖ Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.today())
    jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
    deskripsi = st.text_input("Deskripsi")

    if st.button("Simpan Pengeluaran"):
        new_id = int(df_keluar["ID"].max()) + 1 if not df_keluar.empty else 1
        new_row = {
            "ID": new_id,
            "Tanggal": tanggal.strftime("%Y-%m-%d"),
            "Jumlah": jumlah,
            "Deskripsi": deskripsi
        }
        df_keluar = pd.concat([df_keluar, pd.DataFrame([new_row])], ignore_index=True)
        save_sheet(sheet_pengeluaran, df_keluar)
        st.success("✅ Data pengeluaran berhasil disimpan!")
