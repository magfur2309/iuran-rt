import streamlit as st
import sqlite3
from datetime import date

# Inisialisasi database
conn = sqlite3.connect('iuran_rt.db', check_same_thread=False)
c = conn.cursor()

# Buat tabel jika belum ada
c.execute('''
    CREATE TABLE IF NOT EXISTS warga (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT,
        alamat TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS pembayaran (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warga_id INTEGER,
        kategori TEXT,
        bulan TEXT,
        jumlah REAL,
        tanggal_bayar TEXT,
        FOREIGN KEY(warga_id) REFERENCES warga(id)
    )
''')
conn.commit()

st.title("Aplikasi Iuran RT")

menu = st.sidebar.selectbox("Menu", ["Data Warga", "Pembayaran", "Laporan"])

if menu == "Data Warga":
    st.header("Data Warga")
    nama = st.text_input("Nama")
    alamat = st.text_input("Alamat")
    if st.button("Tambah Warga"):
        c.execute("INSERT INTO warga (nama, alamat) VALUES (?, ?)", (nama, alamat))
        conn.commit()
        st.success("Berhasil menambah warga!")
    st.subheader("Daftar Warga")
    warga = c.execute("SELECT * FROM warga").fetchall()
    for w in warga:
        st.write(f"{w[1]} - {w[2]}")

elif menu == "Pembayaran":
    st.header("Pembayaran Iuran")
    warga = c.execute("SELECT * FROM warga").fetchall()
    warga_dict = {f"{w[1]} - {w[2]}": w[0] for w in warga}
    selected_warga = st.selectbox("Pilih Warga", list(warga_dict.keys()))
    kategori = st.selectbox("Kategori", ["pokok", "kas gang"])
    bulan = st.text_input("Bulan (contoh: Juni 2025)")
    jumlah = st.number_input("Jumlah", min_value=0.0)
    tanggal_bayar = st.date_input("Tanggal Bayar", value=date.today())
    if st.button("Simpan Pembayaran"):
        c.execute("INSERT INTO pembayaran (warga_id, kategori, bulan, jumlah, tanggal_bayar) VALUES (?, ?, ?, ?, ?)",
                  (warga_dict[selected_warga], kategori, bulan, jumlah, tanggal_bayar.strftime('%Y-%m-%d')))
        conn.commit()
        st.success("Pembayaran berhasil disimpan!")

elif menu == "Laporan":
    st.header("Laporan Pembayaran")
    pembayaran = c.execute('''
        SELECT warga.nama, pembayaran.kategori, pembayaran.bulan, pembayaran.jumlah, pembayaran.tanggal_bayar
        FROM pembayaran JOIN warga ON pembayaran.warga_id = warga.id
        ORDER BY pembayaran.tanggal_bayar DESC
    ''').fetchall()
    if pembayaran:
        st.table(pembayaran)
    else:
        st.info("Belum ada data pembayaran.")
