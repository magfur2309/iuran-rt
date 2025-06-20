import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import os

# --- File Path CSV ---
FILE_WARGA = "warga.csv"
FILE_IURAN = "iuran_masuk.csv"
FILE_PENGELUARAN = "pengeluaran.csv"

# --- Fungsi Load & Save CSV ---
def load_csv(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columns)

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

# --- Load Data ---
df_warga = load_csv(FILE_WARGA, ["ID", "Nama"])
df_iuran = load_csv(FILE_IURAN, ["ID", "Nama", "Tanggal", "Jumlah", "Kategori"])
df_keluar = load_csv(FILE_PENGELUARAN, ["ID", "Tanggal", "Jumlah", "Deskripsi"])

# --- Login ---
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "warga1": {"password": "warga123", "role": "warga"},
    "warga2": {"password": "warga123", "role": "warga"},
}

if 'login' not in st.session_state:
    st.session_state.login = False
    st.session_state.username = ''
    st.session_state.role = ''

if not st.session_state.login:
    st.set_page_config(page_title="Iuran Kas RT", layout="wide")

    # --- CSS Custom untuk Login ---
    st.markdown("""
        <style>
        body {
            background-color: #111827;
        }
        .stApp {
            background-color: #111827;
            color: white;
        }
        .login-container {
            margin-top: 100px;
            text-align: center;
        }
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

# --- Sidebar Styling & Menu ---
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 10px; border-radius: 10px; background-color: #1f2937; color: white;">
            👤 <b>Login sebagai:</b><br>{st.session_state.username} ({st.session_state.role})
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")
    role = st.session_state.role
    if role == 'admin':
        menu = st.radio("📋 Menu Utama", [
            "Dashboard", "Tambah Iuran", "Lihat Iuran", 
            "Tambah Pengeluaran", "Lihat Pengeluaran",
            "Laporan Status Iuran", "Export Excel"
        ])
    else:
        menu = st.radio("📋 Menu Warga", ["Dashboard", "Laporan Status Iuran"])
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.login = False
        st.session_state.username = ''
        st.session_state.role = ''
        st.rerun()

# --- Dashboard ---
if menu == "Dashboard":
    st.title("📊 Dashboard Keuangan RT")

    df_iuran["Tanggal"] = pd.to_datetime(df_iuran["Tanggal"])
    df_keluar["Tanggal"] = pd.to_datetime(df_keluar["Tanggal"])

    total_masuk = df_iuran["Jumlah"].sum()
    total_keluar = df_keluar["Jumlah"].sum()
    saldo = total_masuk - total_keluar

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Pemasukan", f"Rp {total_masuk:,.0f}")
    col2.metric("💸 Pengeluaran", f"Rp {total_keluar:,.0f}")
    col3.metric("💼 Saldo", f"Rp {saldo:,.0f}")

    df_iuran['Bulan'] = df_iuran['Tanggal'].dt.to_period("M").astype(str)
    df_keluar['Bulan'] = df_keluar['Tanggal'].dt.to_period("M").astype(str)

    masuk_bulanan = df_iuran.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pemasukan")
    keluar_bulanan = df_keluar.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pengeluaran")
    df_grafik = pd.merge(masuk_bulanan, keluar_bulanan, on="Bulan", how="outer").fillna(0).melt(
        id_vars=["Bulan"], var_name="Tipe", value_name="Jumlah")

    chart = alt.Chart(df_grafik).mark_bar().encode(
        x=alt.X("Bulan:O", title="Bulan"),
        y=alt.Y("Jumlah:Q", title="Jumlah (Rp)"),
        color=alt.Color("Tipe:N", scale=alt.Scale(range=["#4CAF50", "#F44336"])),
        tooltip=["Bulan", "Tipe", "Jumlah"]
    ).properties(width="container", title="📈 Grafik Kas Per Bulan")

    st.altair_chart(chart, use_container_width=True)

# --- Tambah Iuran ---
if menu == "Tambah Iuran" and role == "admin":
    st.title("➕ Tambah Iuran")
    nama = st.selectbox("Nama Warga", df_warga["Nama"])
    tanggal = st.date_input("Tanggal", datetime.today())
    kategori = st.selectbox("Kategori Iuran", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"])

    if kategori == "Iuran Pokok":
        jumlah = 35000
    elif kategori == "Iuran Kas Gang":
        jumlah = 15000
    else:
        jumlah = 50000

    if st.button("Simpan Iuran"):
        new_id = len(df_iuran) + 1
        new_row = {
            "ID": new_id,
            "Nama": nama,
            "Tanggal": tanggal,
            "Jumlah": jumlah,
            "Kategori": kategori
        }
        df_iuran = pd.concat([df_iuran, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(df_iuran, FILE_IURAN)
        st.success("✅ Data iuran berhasil disimpan!")

# --- Lihat Iuran ---
if menu == "Lihat Iuran" and role == "admin":
    st.title("📂 Data Iuran Masuk")
    st.dataframe(df_iuran.sort_values("Tanggal", ascending=False), use_container_width=True)

# --- Tambah Pengeluaran ---
if menu == "Tambah Pengeluaran" and role == "admin":
    st.title("➖ Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.today())
    jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
    deskripsi = st.text_input("Deskripsi")

    if st.button("Simpan Pengeluaran"):
        new_id = len(df_keluar) + 1
        new_row = {
            "ID": new_id,
            "Tanggal": tanggal,
            "Jumlah": jumlah,
            "Deskripsi": deskripsi
        }
        df_keluar = pd.concat([df_keluar, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(df_keluar, FILE_PENGELUARAN)
        st.success("✅ Data pengeluaran berhasil disimpan!")

# --- Lihat Pengeluaran ---
if menu == "Lihat Pengeluaran" and role == "admin":
    st.title("📁 Data Pengeluaran")
    st.dataframe(df_keluar.sort_values("Tanggal", ascending=False), use_container_width=True)

# --- Laporan Status Iuran ---
if menu == "Laporan Status Iuran":
    st.title("📝 Laporan Status Iuran")

    df_iuran["Bulan"] = pd.to_datetime(df_iuran["Tanggal"]).dt.to_period("M")
    bulan_terakhir = df_iuran["Bulan"].max()

    laporan = []
    for _, row in df_warga.iterrows():
        warga = row["Nama"]
        bayar = df_iuran[(df_iuran["Nama"] == warga) & (df_iuran["Bulan"] == bulan_terakhir)]
        status = "Lunas" if not bayar.empty else "Belum Lunas"
        laporan.append({"Nama": warga, "Bulan": str(bulan_terakhir), "Status": status})

    df_laporan = pd.DataFrame(laporan)
    st.dataframe(df_laporan, use_container_width=True)

# --- Export Excel ---
if menu == "Export Excel" and role == "admin":
    st.title("⬇️ Export Data ke Excel")
    tab1, tab2 = st.tabs(["Iuran", "Pengeluaran"])
    with tab1:
        st.download_button("Download Iuran", df_iuran.to_csv(index=False), "iuran.csv", "text/csv")
    with tab2:
        st.download_button("Download Pengeluaran", df_keluar.to_csv(index=False), "pengeluaran.csv", "text/csv")
