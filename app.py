import streamlit as st
import pandas as pd
from datetime import datetime
import os
import calendar

# --- File Paths
FILE_WARGA = "warga.csv"
FILE_MASUK = "kas_masuk.csv"
FILE_KELUAR = "kas_keluar.csv"

# --- Inisialisasi Awal
def init_file(file, columns):
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

def load_csv(file):
    return pd.read_csv(file)

def save_csv(df, file):
    df.to_csv(file, index=False)

# --- Setup Data
init_file(FILE_WARGA, ["Nama"])
init_file(FILE_MASUK, ["ID", "Nama", "Tanggal", "Jumlah", "Kategori"])
init_file(FILE_KELUAR, ["ID", "Keterangan", "Tanggal", "Jumlah"])

df_warga = load_csv(FILE_WARGA)
df_masuk = load_csv(FILE_MASUK)
df_keluar = load_csv(FILE_KELUAR)

# --- Sidebar Menu
st.sidebar.title("📋 Menu")
menu = st.sidebar.radio("Pilih Halaman", [
    "Tambah Iuran",
    "Tambah Pengeluaran",
    "Laporan Iuran Warga",
    "Rekap & Grafik"
])

# --- Tambah Iuran
if menu == "Tambah Iuran":
    st.header("💰 Tambah Iuran Warga")
    nama = st.selectbox("Nama Warga", df_warga["Nama"])
    kategori = st.selectbox("Kategori Iuran", ["Iuran Pokok", "Iuran Kas Gang"])
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    tanggal = st.date_input("Tanggal", datetime.today())

    if st.button("Simpan Iuran"):
        new_id = str(int(df_masuk["ID"].max()) + 1) if not df_masuk.empty else "1"
        new_row = pd.DataFrame([[new_id, nama, tanggal, jumlah, kategori]],
                               columns=["ID", "Nama", "Tanggal", "Jumlah", "Kategori"])
        df_masuk = pd.concat([df_masuk, new_row], ignore_index=True)
        save_csv(df_masuk, FILE_MASUK)
        st.success("✅ Iuran berhasil ditambahkan.")

# --- Tambah Pengeluaran
elif menu == "Tambah Pengeluaran":
    st.header("💸 Tambah Pengeluaran RT")
    keterangan = st.text_input("Keterangan")
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    tanggal = st.date_input("Tanggal", datetime.today())

    if st.button("Simpan Pengeluaran"):
        new_id = str(int(df_keluar["ID"].max()) + 1) if not df_keluar.empty else "1"
        new_row = pd.DataFrame([[new_id, keterangan, tanggal, jumlah]],
                               columns=["ID", "Keterangan", "Tanggal", "Jumlah"])
        df_keluar = pd.concat([df_keluar, new_row], ignore_index=True)
        save_csv(df_keluar, FILE_KELUAR)
        st.success("✅ Pengeluaran berhasil ditambahkan.")

# --- Laporan Iuran
elif menu == "Laporan Iuran Warga":
    st.header("📑 Laporan Status Iuran Warga")
    bulan = st.selectbox("Pilih Bulan", range(1, 13), format_func=lambda x: calendar.month_name[x])
    tahun = st.number_input("Tahun", value=datetime.today().year)

    df_masuk["Tanggal"] = pd.to_datetime(df_masuk["Tanggal"])
    df_filtered = df_masuk[(df_masuk["Tanggal"].dt.month == bulan) &
                           (df_masuk["Tanggal"].dt.year == tahun)]

    kategori_list = ["Iuran Pokok", "Iuran Kas Gang"]

    laporan = pd.DataFrame({"Nama": df_warga["Nama"]})

    for kategori in kategori_list:
        def cek_lunas(nama):
            bayar = df_filtered[(df_filtered["Nama"] == nama) & (df_filtered["Kategori"] == kategori)]
            return "Lunas" if not bayar.empty else "Belum Lunas"
        laporan[kategori] = laporan["Nama"].apply(cek_lunas)

    st.dataframe(laporan)

# --- Rekap dan Grafik
elif menu == "Rekap & Grafik":
    st.header("📊 Rekap Kas RT")
    df_masuk["Tanggal"] = pd.to_datetime(df_masuk["Tanggal"])
    df_keluar["Tanggal"] = pd.to_datetime(df_keluar["Tanggal"])

    total_masuk = df_masuk["Jumlah"].sum()
    total_keluar = df_keluar["Jumlah"].sum()
    saldo = total_masuk - total_keluar

    st.metric("Total Iuran Masuk", f"Rp {total_masuk:,.0f}")
    st.metric("Total Pengeluaran", f"Rp {total_keluar:,.0f}")
    st.metric("Saldo Kas RT", f"Rp {saldo:,.0f}")

    # Grafik per bulan (opsional dengan plotly/matplotlib jika ingin)
