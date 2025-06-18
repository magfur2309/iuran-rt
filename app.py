import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import calendar

# --- File Path
FILE_WARGA = "warga.csv"
FILE_MASUK = "kas_masuk.csv"
FILE_KELUAR = "kas_keluar.csv"

# --- Setup File Awal
def init_file(file, columns):
    if not os.path.exists(file):
        pd.DataFrame(columns=columns).to_csv(file, index=False)

def load_csv(file):
    return pd.read_csv(file)

def save_csv(df, file):
    df.to_csv(file, index=False)

# --- Inisialisasi
init_file(FILE_WARGA, ["Nama"])
init_file(FILE_MASUK, ["ID", "Nama", "Tanggal", "Jumlah", "Kategori"])
init_file(FILE_KELUAR, ["ID", "Keterangan", "Tanggal", "Jumlah"])

# --- Load Data
df_warga = load_csv(FILE_WARGA)
df_masuk = load_csv(FILE_MASUK)
df_keluar = load_csv(FILE_KELUAR)

# --- Sidebar Menu
st.sidebar.title("📋 Menu")
menu = st.sidebar.radio("Pilih Halaman", [
    "Tambah Iuran",
    "Tambah Pengeluaran",
    "Lihat & Kelola Data",
    "Laporan Status Iuran",
    "Rekap & Grafik"
])

# ... (IMPORT DAN SETUP FILE SAMA SEPERTI SEBELUMNYA)

# --- Tambah Iuran
if menu == "Tambah Iuran":
    st.header("💰 Tambah Iuran Warga")
    nama = st.selectbox("Nama Warga", df_warga["Nama"])
    kategori = st.selectbox("Kategori Iuran", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"])
    jumlah = st.number_input("Jumlah (Rp)", min_value=0)
    tanggal = st.date_input("Tanggal", datetime.today())

    if st.button("Simpan Iuran"):
        new_id = str(int(df_masuk["ID"].max()) + 1) if not df_masuk.empty else "1"
        new_row = pd.DataFrame([[new_id, nama, tanggal, jumlah, kategori]],
                               columns=["ID", "Nama", "Tanggal", "Jumlah", "Kategori"])
        df_masuk = pd.concat([df_masuk, new_row], ignore_index=True)
        save_csv(df_masuk, FILE_MASUK)
        st.success("✅ Iuran berhasil ditambahkan.")

# --- Laporan Status Iuran (DIPERBARUI)
elif menu == "Laporan Status Iuran":
    st.header("📑 Status Iuran Per Warga")
    bulan = st.selectbox("Pilih Bulan", range(1, 13), format_func=lambda x: calendar.month_name[x])
    tahun = st.number_input("Tahun", value=datetime.today().year)

    df_masuk["Tanggal"] = pd.to_datetime(df_masuk["Tanggal"])
    df_filtered = df_masuk[(df_masuk["Tanggal"].dt.month == bulan) &
                           (df_masuk["Tanggal"].dt.year == tahun)]

    kategori_list = ["Iuran Pokok", "Iuran Kas Gang"]
    laporan = pd.DataFrame({"Nama": df_warga["Nama"]})

    def cek_status(nama, kategori):
        # Jika bayar gabungan, otomatis dianggap lunas semua
        bayar_gabungan = not df_filtered[(df_filtered["Nama"] == nama) & (df_filtered["Kategori"] == "Iuran Pokok+Kas Gang")].empty
        if bayar_gabungan:
            return "Lunas"
        # Cek apakah bayar kategori terpisah
        bayar_kategori = not df_filtered[(df_filtered["Nama"] == nama) & (df_filtered["Kategori"] == kategori)].empty
        return "Lunas" if bayar_kategori else "Belum Lunas"

    for kategori in kategori_list:
        laporan[kategori] = laporan["Nama"].apply(lambda nama: cek_status(nama, kategori))

    st.dataframe(laporan)


# --- Grafik Interaktif
elif menu == "Rekap & Grafik":
    st.header("📊 Grafik Kas RT")

    df_masuk["Tanggal"] = pd.to_datetime(df_masuk["Tanggal"])
    df_keluar["Tanggal"] = pd.to_datetime(df_keluar["Tanggal"])

    # Rekap Bulanan
    df_masuk["Bulan"] = df_masuk["Tanggal"].dt.strftime("%Y-%m")
    df_keluar["Bulan"] = df_keluar["Tanggal"].dt.strftime("%Y-%m")

    total_masuk = df_masuk.groupby("Bulan")["Jumlah"].sum().reset_index(name="Iuran Masuk")
    total_keluar = df_keluar.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pengeluaran")

    df_merge = pd.merge(total_masuk, total_keluar, on="Bulan", how="outer").fillna(0)
    df_merge["Saldo"] = df_merge["Iuran Masuk"] - df_merge["Pengeluaran"]

    fig = px.line(df_merge, x="Bulan", y=["Iuran Masuk", "Pengeluaran", "Saldo"],
                  markers=True, title="Grafik Kas Bulanan")
    st.plotly_chart(fig, use_container_width=True)

    st.metric("Total Masuk", f"Rp {df_masuk['Jumlah'].sum():,.0f}")
    st.metric("Total Keluar", f"Rp {df_keluar['Jumlah'].sum():,.0f}")
    st.metric("Saldo Akhir", f"Rp {df_masuk['Jumlah'].sum() - df_keluar['Jumlah'].sum():,.0f}")
