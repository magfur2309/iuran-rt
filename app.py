import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from google_sheets import connect_to_gsheet, load_sheet, save_sheet

# Koneksi ke Google Sheets
sheet = connect_to_gsheet("11ZCpjZe3vsFG3Ye-c1kSsYHTk6Z_Ktc3Z6YczH4lHIk")
sheet_warga = sheet.worksheet("Warga")
sheet_iuran = sheet.worksheet("Iuran")
sheet_pengeluaran = sheet.worksheet("Pengeluaran")

# Load data
df_warga = load_sheet(sheet_warga)
df_iuran = load_sheet(sheet_iuran)
df_keluar = load_sheet(sheet_pengeluaran)

# Login
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "warga1": {"password": "warga123", "role": "warga"},
}

if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.login:
    st.set_page_config("Iuran Kas RT", layout="wide")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.login = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("Username atau password salah.")
    st.stop()

# Menu
role = st.session_state.role
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Tambah Iuran", "Tambah Pengeluaran", "Laporan Status Iuran"] if role == "admin" else ["Dashboard", "Laporan Status Iuran"])

# Tambah Iuran
if menu == "Tambah Iuran" and role == "admin":
    st.title("➕ Tambah Iuran")
    nama = st.selectbox("Nama Warga", df_warga["Nama"])
    tanggal = st.date_input("Tanggal", datetime.today())
    kategori = st.selectbox("Kategori", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang", "Lain-lain"])
    jumlah = st.number_input("Jumlah", 0, step=1000, value={"Iuran Pokok":35000,"Iuran Kas Gang":15000,"Iuran Pokok+Kas Gang":50000}.get(kategori,0))
    if st.button("Simpan Iuran"):
        new_id = df_iuran["ID"].max()+1 if not df_iuran.empty else 1
        new_row = {"ID": new_id, "Nama": nama, "Tanggal": tanggal.strftime("%Y-%m-%d"), "Jumlah": jumlah, "Kategori": kategori}
        df_iuran = pd.concat([df_iuran, pd.DataFrame([new_row])], ignore_index=True)
        save_sheet(sheet_iuran, df_iuran)
        st.success("✅ Tersimpan")

# Tambah Pengeluaran
if menu == "Tambah Pengeluaran" and role == "admin":
    st.title("➖ Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.today())
    jumlah = st.number_input("Jumlah (Rp)", 0, step=1000)
    deskripsi = st.text_input("Deskripsi")
    if st.button("Simpan Pengeluaran"):
        new_id = df_keluar["ID"].max()+1 if not df_keluar.empty else 1
        new_row = {"ID": new_id, "Tanggal": tanggal.strftime("%Y-%m-%d"), "Jumlah": jumlah, "Deskripsi": deskripsi}
        df_keluar = pd.concat([df_keluar, pd.DataFrame([new_row])], ignore_index=True)
        save_sheet(sheet_pengeluaran, df_keluar)
        st.success("✅ Tersimpan")

# Laporan Status
if menu == "Laporan Status Iuran":
    st.title("📝 Status Iuran")
    df_iuran["Tanggal"] = pd.to_datetime(df_iuran["Tanggal"], errors="coerce")
    df_iuran["Bulan"] = df_iuran["Tanggal"].dt.to_period("M")
    bulan_terakhir = df_iuran["Bulan"].max()
    laporan = []
    for _, row in df_warga.iterrows():
        status = "Lunas" if not df_iuran[(df_iuran["Nama"]==row["Nama"]) & (df_iuran["Bulan"]==bulan_terakhir)].empty else "Belum Lunas"
        laporan.append({"Nama": row["Nama"], "Bulan": str(bulan_terakhir), "Status": status})
    st.dataframe(pd.DataFrame(laporan), use_container_width=True)

# Dashboard
if menu == "Dashboard":
    st.title("📊 Dashboard")
    df_iuran["Tanggal"] = pd.to_datetime(df_iuran["Tanggal"], errors="coerce")
    df_keluar["Tanggal"] = pd.to_datetime(df_keluar["Tanggal"], errors="coerce")
    total_masuk = df_iuran["Jumlah"].sum()
    total_keluar = df_keluar["Jumlah"].sum()
    saldo = total_masuk - total_keluar
    st.metric("💰 Pemasukan", f"Rp {total_masuk:,.0f}")
    st.metric("💸 Pengeluaran", f"Rp {total_keluar:,.0f}")
    st.metric("💼 Saldo", f"Rp {saldo:,.0f}")

    df_iuran["Bulan"] = df_iuran["Tanggal"].dt.to_period("M").astype(str)
    df_keluar["Bulan"] = df_keluar["Tanggal"].dt.to_period("M").astype(str)
    masuk = df_iuran.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pemasukan")
    keluar = df_keluar.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pengeluaran")
    df_grafik = pd.merge(masuk, keluar, on="Bulan", how="outer").fillna(0).melt("Bulan", var_name="Tipe", value_name="Jumlah")
    chart = alt.Chart(df_grafik).mark_bar().encode(
        x="Bulan", y="Jumlah", color="Tipe", tooltip=["Bulan", "Tipe", "Jumlah"]
    ).properties(title="📈 Grafik Kas Per Bulan")
    st.altair_chart(chart, use_container_width=True)
