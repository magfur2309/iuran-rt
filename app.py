import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import os

# File CSV
FILE_WARGA = "warga.csv"
FILE_IURAN = "iuran_masuk.csv"
FILE_PENGELUARAN = "pengeluaran.csv"

# Load & Save
def load_csv(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(columns=columns)

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

# Load data
df_warga = load_csv(FILE_WARGA, ["ID", "Nama"])
df_iuran = load_csv(FILE_IURAN, ["ID", "Nama", "Tanggal", "Jumlah", "Kategori"])
df_keluar = load_csv(FILE_PENGELUARAN, ["ID", "Tanggal", "Jumlah", "Deskripsi"])

# Users
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "warga1": {"password": "warga123", "role": "warga"},
}

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.username = ""
    st.session_state.role = ""

# LOGIN
if not st.session_state.login:
    st.markdown("<h2 style='text-align: center;'>🔐 Login Iuran Kas RT</h2>", unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username in users and users[username]["password"] == password:
                st.session_state.login = True
                st.session_state.username = username
                st.session_state.role = users[username]["role"]
                st.experimental_rerun()
            else:
                st.error("Username atau Password salah.")
    st.stop()

# SIDEBAR
st.sidebar.success(f"Login sebagai: {st.session_state.username} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    for k in ["login", "username", "role"]:
        st.session_state[k] = False if k == "login" else ""
    st.rerun()

# Menu
role = st.session_state.role
if role == "admin":
    menu = st.sidebar.radio("Menu", [
        "Dashboard", "Tambah Iuran", "Lihat Iuran", "Tambah Pengeluaran",
        "Lihat Pengeluaran", "Status Iuran", "Export Data"
    ])
else:
    menu = st.sidebar.radio("Menu", ["Dashboard", "Status Iuran"])

# DASHBOARD
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

    # Grafik
    df_iuran['Bulan'] = df_iuran['Tanggal'].dt.to_period("M").astype(str)
    df_keluar['Bulan'] = df_keluar['Tanggal'].dt.to_period("M").astype(str)
    masuk = df_iuran.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pemasukan")
    keluar = df_keluar.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pengeluaran")
    df_chart = pd.merge(masuk, keluar, on="Bulan", how="outer").fillna(0).melt(id_vars="Bulan", var_name="Tipe", value_name="Jumlah")

    chart = alt.Chart(df_chart).mark_bar().encode(
        x="Bulan:O", y="Jumlah:Q", color="Tipe:N", tooltip=["Bulan", "Tipe", "Jumlah"]
    ).properties(width="container", title="Grafik Keuangan Bulanan")

    st.altair_chart(chart, use_container_width=True)

# TAMBAH IURAN
if menu == "Tambah Iuran" and role == "admin":
    st.title("➕ Tambah Iuran Warga")
    nama = st.selectbox("Nama", df_warga["Nama"])
    tanggal = st.date_input("Tanggal", datetime.today())
    kategori = st.selectbox("Kategori", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"])
    jumlah = 50000 if kategori == "Iuran Pokok+Kas Gang" else (35000 if kategori == "Iuran Pokok" else 15000)

    if st.button("Simpan"):
        new_id = len(df_iuran) + 1
        df_iuran.loc[len(df_iuran)] = [new_id, nama, tanggal, jumlah, kategori]
        save_csv(df_iuran, FILE_IURAN)
        st.success("✅ Iuran berhasil ditambahkan.")

# LIHAT IURAN
if menu == "Lihat Iuran" and role == "admin":
    st.title("📄 Data Iuran Masuk")
    st.dataframe(df_iuran.sort_values("Tanggal", ascending=False), use_container_width=True)

# TAMBAH PENGELUARAN
if menu == "Tambah Pengeluaran" and role == "admin":
    st.title("➖ Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.today())
    jumlah = st.number_input("Jumlah", min_value=0)
    deskripsi = st.text_input("Deskripsi")
    if st.button("Simpan"):
        new_id = len(df_keluar) + 1
        df_keluar.loc[len(df_keluar)] = [new_id, tanggal, jumlah, deskripsi]
        save_csv(df_keluar, FILE_PENGELUARAN)
        st.success("✅ Pengeluaran disimpan.")

# LIHAT PENGELUARAN
if menu == "Lihat Pengeluaran" and role == "admin":
    st.title("📄 Data Pengeluaran")
    st.dataframe(df_keluar.sort_values("Tanggal", ascending=False), use_container_width=True)

# STATUS IURAN
if menu == "Status Iuran":
    st.title("📋 Status Iuran Warga")
    df_iuran["Tanggal"] = pd.to_datetime(df_iuran["Tanggal"])
    df_iuran["Bulan"] = df_iuran["Tanggal"].dt.to_period("M")
    bulan_terakhir = df_iuran["Bulan"].max()
    laporan = []
    for _, row in df_warga.iterrows():
        warga = row["Nama"]
        data = df_iuran[(df_iuran["Nama"] == warga) & (df_iuran["Bulan"] == bulan_terakhir)]
        status = "Lunas" if not data.empty else "Belum Lunas"
        laporan.append({"Nama": warga, "Bulan": str(bulan_terakhir), "Status": status})
    st.dataframe(pd.DataFrame(laporan), use_container_width=True)

# EXPORT
if menu == "Export Data" and role == "admin":
    st.title("⬇️ Export Data ke Excel")
    df_iuran_sorted = df_iuran.sort_values("Tanggal", ascending=False)
    df_keluar_sorted = df_keluar.sort_values("Tanggal", ascending=False)
    with pd.ExcelWriter("data_kas_rt.xlsx") as writer:
        df_warga.to_excel(writer, index=False, sheet_name="Warga")
        df_iuran_sorted.to_excel(writer, index=False, sheet_name="Iuran")
        df_keluar_sorted.to_excel(writer, index=False, sheet_name="Pengeluaran")
    with open("data_kas_rt.xlsx", "rb") as f:
        st.download_button("Download Excel", f, file_name="kas_rt.xlsx")
