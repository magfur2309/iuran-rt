import streamlit as st
import pandas as pd
import hashlib
import calendar
from datetime import datetime
import os

# --- FILE PATH ---
FILE_WARGA = "warga.csv"
FILE_IURAN = "iuran_masuk.csv"
FILE_PENGELUARAN = "pengeluaran.csv"

# --- SETUP DATA ---
def load_csv(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columns)

df_warga = load_csv(FILE_WARGA, ["ID", "Nama"])
df_masuk = load_csv(FILE_IURAN, ["ID", "Nama", "Tanggal", "Jumlah", "Kategori"])
df_keluar = load_csv(FILE_PENGELUARAN, ["ID", "Tanggal", "Jumlah", "Deskripsi"])

# --- SIMPAN ---
def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

# --- USER LOGIN ---
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
    st.title("🔐 Login Aplikasi Iuran Kas RT")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in users and password == users[username]['password']:
            st.session_state.login = True
            st.session_state.username = username
            st.session_state.role = users[username]['role']
            st.experimental_rerun()
        else:
            st.error("Username atau password salah.")
else:
    role = st.session_state.role
    st.sidebar.write(f"👤 Login sebagai: `{st.session_state.username}` ({role})")
    if st.sidebar.button("Logout"):
        for key in ["login", "username", "role"]:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

    # --- MENU ---
    if role == "admin":
        menu = st.sidebar.radio("📋 Menu", [
            "Dashboard", "Tambah Iuran", "Lihat & Kelola Iuran",
            "Tambah Pengeluaran", "Lihat & Kelola Pengeluaran",
            "Laporan Status Iuran", "Export Excel"
        ])
    else:
        menu = st.sidebar.radio("📋 Menu", [
            "Dashboard", "Laporan Status Iuran", "Lihat Pengeluaran"
        ])

    # --- DASHBOARD ---
    if menu == "Dashboard":
        st.header("📊 Dashboard Kas RT")

        # Konversi tanggal
        df_masuk["Tanggal"] = pd.to_datetime(df_masuk["Tanggal"])
        df_keluar["Tanggal"] = pd.to_datetime(df_keluar["Tanggal"])

        total_masuk = df_masuk["Jumlah"].sum()
        total_keluar = df_keluar["Jumlah"].sum()
        saldo = total_masuk - total_keluar

        df_masuk['Bulan'] = df_masuk['Tanggal'].dt.to_period('M')
        df_keluar['Bulan'] = df_keluar['Tanggal'].dt.to_period('M')

        pemasukan_bulanan = df_masuk.groupby("Bulan")["Jumlah"].sum()
        pengeluaran_bulanan = df_keluar.groupby("Bulan")["Jumlah"].sum()

        df_summary = pd.DataFrame({
            "Pemasukan": pemasukan_bulanan,
            "Pengeluaran": pengeluaran_bulanan
        }).fillna(0)

        st.metric("Total Pemasukan", f"Rp {total_masuk:,.0f}")
        st.metric("Total Pengeluaran", f"Rp {total_keluar:,.0f}")
        st.metric("Saldo Kas Saat Ini", f"Rp {saldo:,.0f}")

        st.subheader("📈 Grafik Kas Per Bulan")
        st.bar_chart(df_summary)

        st.subheader("🕘 Iuran Masuk Terbaru")
        st.dataframe(df_masuk.sort_values(by="Tanggal", ascending=False).head(5))

    # --- TAMBAH IURAN ---
    elif menu == "Tambah Iuran":
        st.header("💰 Tambah Iuran Warga")
        nama = st.selectbox("Nama Warga", df_warga["Nama"])
        kategori = st.selectbox("Kategori Iuran", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"])
        jumlah_default = {"Iuran Pokok": 35000, "Iuran Kas Gang": 15000, "Iuran Pokok+Kas Gang": 50000}
        jumlah = st.number_input("Jumlah (Rp)", min_value=0, value=jumlah_default[kategori])
        tanggal = st.date_input("Tanggal", datetime.today())

        if st.button("Simpan Iuran"):
            new_id = str(int(df_masuk["ID"].max()) + 1) if not df_masuk.empty else "1"
            new_row = pd.DataFrame([[new_id, nama, tanggal, jumlah, kategori]],
                                   columns=["ID", "Nama", "Tanggal", "Jumlah", "Kategori"])
            df_masuk = pd.concat([df_masuk, new_row], ignore_index=True)
            save_csv(df_masuk, FILE_IURAN)
            st.success("✅ Iuran berhasil ditambahkan.")

    # --- LIHAT & KELOLA IURAN ---
    elif menu == "Lihat & Kelola Iuran":
        st.header("📄 Data Iuran Masuk")
        st.dataframe(df_masuk)

        if st.checkbox("✏️ Edit / Hapus Iuran"):
            row_id = st.text_input("Masukkan ID untuk Edit atau Hapus:")
            if row_id:
                edit_data = df_masuk[df_masuk["ID"] == row_id]
                if not edit_data.empty:
                    nama = st.selectbox("Nama", df_warga["Nama"], index=df_warga[df_warga["Nama"] == edit_data.iloc[0]["Nama"]].index[0])
                    kategori = st.selectbox("Kategori", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"],
                                            index=["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"].index(edit_data.iloc[0]["Kategori"]))
                    jumlah = st.number_input("Jumlah", value=int(edit_data.iloc[0]["Jumlah"]))
                    tanggal = st.date_input("Tanggal", pd.to_datetime(edit_data.iloc[0]["Tanggal"]))
                    if st.button("Update"):
                        df_masuk.loc[df_masuk["ID"] == row_id, ["Nama", "Tanggal", "Jumlah", "Kategori"]] = [nama, tanggal, jumlah, kategori]
                        save_csv(df_masuk, FILE_IURAN)
                        st.success("✅ Data diperbarui.")
                    if st.button("Hapus"):
                        df_masuk = df_masuk[df_masuk["ID"] != row_id]
                        save_csv(df_masuk, FILE_IURAN)
                        st.success("🗑️ Data dihapus.")

    # --- TAMBAH PENGELUARAN ---
    elif menu == "Tambah Pengeluaran":
        st.header("💸 Tambah Pengeluaran")
        tanggal = st.date_input("Tanggal", datetime.today())
        jumlah = st.number_input("Jumlah (Rp)", min_value=0)
        deskripsi = st.text_input("Deskripsi")
        if st.button("Simpan Pengeluaran"):
            new_id = str(int(df_keluar["ID"].max()) + 1) if not df_keluar.empty else "1"
            new_row = pd.DataFrame([[new_id, tanggal, jumlah, deskripsi]],
                                   columns=["ID", "Tanggal", "Jumlah", "Deskripsi"])
            df_keluar = pd.concat([df_keluar, new_row], ignore_index=True)
            save_csv(df_keluar, FILE_PENGELUARAN)
            st.success("✅ Pengeluaran berhasil ditambahkan.")

    # --- LIHAT & KELOLA PENGELUARAN ---
    elif menu == "Lihat & Kelola Pengeluaran":
        st.header("📄 Data Pengeluaran")
        st.dataframe(df_keluar)

        if st.checkbox("✏️ Edit / Hapus Pengeluaran"):
            row_id = st.text_input("Masukkan ID untuk Edit atau Hapus:")
            if row_id:
                edit_data = df_keluar[df_keluar["ID"] == row_id]
                if not edit_data.empty:
                    tanggal = st.date_input("Tanggal", pd.to_datetime(edit_data.iloc[0]["Tanggal"]))
                    jumlah = st.number_input("Jumlah", value=int(edit_data.iloc[0]["Jumlah"]))
                    deskripsi = st.text_input("Deskripsi", value=edit_data.iloc[0]["Deskripsi"])
                    if st.button("Update"):
                        df_keluar.loc[df_keluar["ID"] == row_id, ["Tanggal", "Jumlah", "Deskripsi"]] = [tanggal, jumlah, deskripsi]
                        save_csv(df_keluar, FILE_PENGELUARAN)
                        st.success("✅ Data diperbarui.")
                    if st.button("Hapus"):
                        df_keluar = df_keluar[df_keluar["ID"] != row_id]
                        save_csv(df_keluar, FILE_PENGELUARAN)
                        st.success("🗑️ Data dihapus.")

    # --- LIHAT PENGELUARAN (Warga) ---
    elif menu == "Lihat Pengeluaran":
        st.header("📄 Data Pengeluaran")
        st.dataframe(df_keluar)

    # --- LAPORAN STATUS IURAN ---
    elif menu == "Laporan Status Iuran":
        st.header("📑 Status Iuran Per Warga")
        bulan = st.selectbox("Pilih Bulan", list(calendar.month_name)[1:], index=datetime.today().month - 1)
        tahun = st.selectbox("Pilih Tahun", list(range(2020, datetime.today().year + 1)), index=5)

        bulan_num = list(calendar.month_name).index(bulan)
        df_masuk["Tanggal"] = pd.to_datetime(df_masuk["Tanggal"])
        df_filtered = df_masuk[(df_masuk["Tanggal"].dt.month == bulan_num) & (df_masuk["Tanggal"].dt.year == tahun)]

        kategori_list = ["Iuran Pokok", "Iuran Kas Gang"]
        laporan = pd.DataFrame({"Nama": df_warga["Nama"]})

        def cek_status(nama, kategori):
            gabung = df_filtered[(df_filtered["Nama"] == nama) & (df_filtered["Kategori"] == "Iuran Pokok+Kas Gang")]
            if not gabung.empty:
                return "Lunas"
            bayar = df_filtered[(df_filtered["Nama"] == nama) & (df_filtered["Kategori"] == kategori)]
            return "Lunas" if not bayar.empty else "Belum Lunas"

        for kategori in kategori_list:
            laporan[kategori] = laporan["Nama"].apply(lambda nama: cek_status(nama, kategori))

        st.dataframe(laporan)

    # --- EXPORT EXCEL ---
    elif menu == "Export Excel":
        st.header("📤 Export Data ke Excel")
        with pd.ExcelWriter("data_iuran_export.xlsx") as writer:
            df_warga.to_excel(writer, sheet_name="Warga", index=False)
            df_masuk.to_excel(writer, sheet_name="Iuran", index=False)
            df_keluar.to_excel(writer, sheet_name="Pengeluaran", index=False)
        with open("data_iuran_export.xlsx", "rb") as f:
            st.download_button("Download Excel", f, file_name="laporan_kas_rt.xlsx")
