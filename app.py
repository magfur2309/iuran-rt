import streamlit as st
import pandas as pd
from datetime import datetime
import os
import hashlib
import calendar
import plotly.express as px

# --- CONFIG
DATA_MASUK = "kas_masuk.csv"
DATA_KELUAR = "kas_keluar.csv"

USERS = {
    "admin": "admin123",
    "warga1": "warga123",
    "warga2": "warga456"
}

# --- FILE HANDLING
def init_file(path, columns):
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_csv(path, index=False)

def load_csv(path):
    return pd.read_csv(path)

def save_csv(df, path):
    df.to_csv(path, index=False)

init_file(DATA_MASUK, ["ID", "Nama", "Tanggal", "Jumlah"])
init_file(DATA_KELUAR, ["ID", "Keterangan", "Tanggal", "Jumlah"])

# --- AUTHENTICATION
def login():
    st.sidebar.title("🔐 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_btn = st.sidebar.button("Login")
    
    if login_btn:
        if username in USERS and USERS[username] == password:
            st.session_state["user"] = username
            st.success(f"Selamat datang, {username}!")
        else:
            st.error("Username atau password salah.")

def logout():
    if st.sidebar.button("Logout"):
        st.session_state.pop("user", None)
        st.rerun()

# --- UTILITIES
def generate_id(df):
    return str(int(df["ID"].max()) + 1) if not df.empty else "1"

def filter_data(df, bulan, nama=None):
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    df_filtered = df[df["Tanggal"].dt.month == bulan]
    if nama:
        df_filtered = df_filtered[df_filtered["Nama"] == nama]
    return df_filtered

# --- MAIN APP
if "user" not in st.session_state:
    login()
    st.stop()

logout()
st.title("💼 Aplikasi Iuran & Kas RT")
user = st.session_state["user"]
df_masuk = load_csv(DATA_MASUK)
df_keluar = load_csv(DATA_KELUAR)

menu = st.sidebar.selectbox("Menu", [
    "Tambah Iuran", "Lihat & Kelola Iuran",
    "Tambah Pengeluaran", "Lihat & Kelola Pengeluaran",
    "Rekap & Grafik", "Export Excel"
])

# --- INPUT PEMASUKAN
if menu == "Tambah Iuran":
    st.subheader("💰 Tambah Iuran")
    nama = st.text_input("Nama Warga", value=user)
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    tanggal = st.date_input("Tanggal", datetime.today())

    if st.button("Simpan Iuran"):
        new_id = generate_id(df_masuk)
        new_row = pd.DataFrame([[new_id, nama, tanggal, jumlah]], columns=["ID", "Nama", "Tanggal", "Jumlah"])
        df_masuk = pd.concat([df_masuk, new_row], ignore_index=True)
        save_csv(df_masuk, DATA_MASUK)
        st.success("Data iuran berhasil disimpan.")

# --- KELOLA PEMASUKAN
elif menu == "Lihat & Kelola Iuran":
    st.subheader("📋 Data Iuran")
    df = df_masuk.copy()
    bulan = st.selectbox("Filter Bulan", range(1, 13), format_func=lambda x: calendar.month_name[x])
    warga = st.selectbox("Filter Warga", ["Semua"] + sorted(df["Nama"].unique().tolist()))
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    df = df[df["Tanggal"].dt.month == bulan]
    if warga != "Semua":
        df = df[df["Nama"] == warga]

    st.dataframe(df)

    if st.checkbox("📝 Edit / Hapus Iuran"):
        edit_id = st.text_input("Masukkan ID Iuran")
        selected = df_masuk[df_masuk["ID"] == edit_id]
        if not selected.empty:
            row = selected.iloc[0]
            nama = st.text_input("Nama", row["Nama"])
            tanggal = st.date_input("Tanggal", pd.to_datetime(row["Tanggal"]))
            jumlah = st.number_input("Jumlah", value=float(row["Jumlah"]))
            if st.button("Update"):
                df_masuk.loc[df_masuk["ID"] == edit_id, ["Nama", "Tanggal", "Jumlah"]] = [nama, tanggal, jumlah]
                save_csv(df_masuk, DATA_MASUK)
                st.success("Berhasil diupdate")
            if st.button("Hapus"):
                df_masuk = df_masuk[df_masuk["ID"] != edit_id]
                save_csv(df_masuk, DATA_MASUK)
                st.success("Data dihapus")

# --- INPUT PENGELUARAN
elif menu == "Tambah Pengeluaran":
    st.subheader("💸 Tambah Pengeluaran")
    ket = st.text_input("Keterangan")
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    tanggal = st.date_input("Tanggal", datetime.today())

    if st.button("Simpan Pengeluaran"):
        new_id = generate_id(df_keluar)
        new_row = pd.DataFrame([[new_id, ket, tanggal, jumlah]], columns=["ID", "Keterangan", "Tanggal", "Jumlah"])
        df_keluar = pd.concat([df_keluar, new_row], ignore_index=True)
        save_csv(df_keluar, DATA_KELUAR)
        st.success("Pengeluaran berhasil disimpan.")

# --- KELOLA PENGELUARAN
elif menu == "Lihat & Kelola Pengeluaran":
    st.subheader("📋 Data Pengeluaran")
    df = df_keluar.copy()
    bulan = st.selectbox("Filter Bulan", range(1, 13), format_func=lambda x: calendar.month_name[x])
    df["Tanggal"] = pd.to_datetime(df["Tanggal"])
    df = df[df["Tanggal"].dt.month == bulan]
    st.dataframe(df)

    if st.checkbox("📝 Edit / Hapus Pengeluaran"):
        edit_id = st.text_input("Masukkan ID Pengeluaran")
        selected = df_keluar[df_keluar["ID"] == edit_id]
        if not selected.empty:
            row = selected.iloc[0]
            ket = st.text_input("Keterangan", row["Keterangan"])
            tanggal = st.date_input("Tanggal", pd.to_datetime(row["Tanggal"]))
            jumlah = st.number_input("Jumlah", value=float(row["Jumlah"]))
            if st.button("Update"):
                df_keluar.loc[df_keluar["ID"] == edit_id, ["Keterangan", "Tanggal", "Jumlah"]] = [ket, tanggal, jumlah]
                save_csv(df_keluar, DATA_KELUAR)
                st.success("Berhasil diupdate")
            if st.button("Hapus"):
                df_keluar = df_keluar[df_keluar["ID"] != edit_id]
                save_csv(df_keluar, DATA_KELUAR)
                st.success("Data dihapus")

# --- REKAP & GRAFIK
elif menu == "Rekap & Grafik":
    st.subheader("📊 Rekap Kas & Grafik Bulanan")
    df_masuk["Tanggal"] = pd.to_datetime(df_masuk["Tanggal"])
    df_keluar["Tanggal"] = pd.to_datetime(df_keluar["Tanggal"])
    
    df_masuk["Bulan"] = df_masuk["Tanggal"].dt.to_period("M").astype(str)
    df_keluar["Bulan"] = df_keluar["Tanggal"].dt.to_period("M").astype(str)

    masuk_group = df_masuk.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pemasukan")
    keluar_group = df_keluar.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pengeluaran")

    rekap = pd.merge(masuk_group, keluar_group, on="Bulan", how="outer").fillna(0)
    rekap["Saldo"] = rekap["Pemasukan"] - rekap["Pengeluaran"]

    st.dataframe(rekap)

    chart = px.bar(rekap, x="Bulan", y=["Pemasukan", "Pengeluaran", "Saldo"], barmode="group", title="Grafik Kas RT")
    st.plotly_chart(chart, use_container_width=True)

    total_in = df_masuk["Jumlah"].sum()
    total_out = df_keluar["Jumlah"].sum()
    saldo = total_in - total_out

    st.metric("Total Pemasukan", f"Rp {total_in:,.0f}")
    st.metric("Total Pengeluaran", f"Rp {total_out:,.0f}")
    st.metric("Saldo Kas RT", f"Rp {saldo:,.0f}")

# --- EXPORT
elif menu == "Export Excel":
    st.subheader("📤 Export Semua Data")
    with pd.ExcelWriter("kas_rt_export.xlsx") as writer:
        df_masuk.to_excel(writer, sheet_name="Pemasukan", index=False)
        df_keluar.to_excel(writer, sheet_name="Pengeluaran", index=False)
    with open("kas_rt_export.xlsx", "rb") as f:
        st.download_button("📥 Download Excel", f, file_name="kas_rt_export.xlsx")
