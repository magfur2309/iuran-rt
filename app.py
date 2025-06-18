role = st.session_state.role

# Menu tidak pakai sidebar, tapi dropdown biasa
if role == "admin":
    menu = st.selectbox("📂 Pilih Menu", [
        "➕ Tambah Iuran", "📋 Data Iuran",
        "➕ Tambah Pengeluaran", "📋 Data Pengeluaran",
        "📊 Grafik Keuangan", "📤 Export Excel", "📑 Laporan Status Iuran"
    ])
else:
    menu = st.selectbox("📂 Pilih Menu", [
        "📑 Laporan Status Iuran", "📋 Data Pengeluaran", "📊 Grafik Keuangan"
    ])

st.divider()

# ======================== MENU AKSI =========================

if menu == "➕ Tambah Iuran":
    st.header("Tambah Data Iuran Warga")
    nama = st.selectbox("Pilih Nama Warga", df_warga["Nama"])
    kategori = st.selectbox("Kategori Iuran", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"])
    default_jumlah = 35000 if kategori == "Iuran Pokok" else 15000 if kategori == "Iuran Kas Gang" else 50000
    jumlah = st.number_input("Jumlah Iuran (Rp)", value=default_jumlah, min_value=0)
    tanggal = st.date_input("Tanggal Pembayaran", value=datetime.today())

    if st.button("💾 Simpan Iuran"):
        new_id = str(int(df_masuk["ID"].max()) + 1) if not df_masuk.empty else "1"
        new_row = pd.DataFrame([[new_id, nama, tanggal, jumlah, kategori]],
                               columns=["ID", "Nama", "Tanggal", "Jumlah", "Kategori"])
        df_masuk = pd.concat([df_masuk, new_row], ignore_index=True)
        save_csv(df_masuk, FILE_IURAN)
        st.success("✅ Data iuran berhasil disimpan.")

elif menu == "📋 Data Iuran":
    st.header("📄 Daftar Iuran Masuk")
    st.dataframe(df_masuk, use_container_width=True)

    if st.checkbox("🛠️ Edit / Hapus Data"):
        row_id = st.text_input("Masukkan ID data yang ingin diedit / dihapus:")
        if row_id:
            target = df_masuk[df_masuk["ID"] == row_id]
            if not target.empty:
                nama = st.selectbox("Nama", df_warga["Nama"], index=df_warga[df_warga["Nama"] == target.iloc[0]["Nama"]].index[0])
                kategori = st.selectbox("Kategori", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"],
                                        index=["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"].index(target.iloc[0]["Kategori"]))
                jumlah = st.number_input("Jumlah", value=int(target.iloc[0]["Jumlah"]))
                tanggal = st.date_input("Tanggal", pd.to_datetime(target.iloc[0]["Tanggal"]))
                if st.button("🔄 Update Data"):
                    df_masuk.loc[df_masuk["ID"] == row_id] = [row_id, nama, tanggal, jumlah, kategori]
                    save_csv(df_masuk, FILE_IURAN)
                    st.success("✅ Data berhasil diperbarui.")
                if st.button("🗑️ Hapus Data"):
                    df_masuk = df_masuk[df_masuk["ID"] != row_id]
                    save_csv(df_masuk, FILE_IURAN)
                    st.success("🗑️ Data berhasil dihapus.")

elif menu == "➕ Tambah Pengeluaran":
    st.header("Tambah Data Pengeluaran")
    tanggal = st.date_input("Tanggal", value=datetime.today())
    jumlah = st.number_input("Jumlah Pengeluaran (Rp)", min_value=0)
    deskripsi = st.text_input("Deskripsi Pengeluaran")
    if st.button("💾 Simpan Pengeluaran"):
        new_id = str(int(df_keluar["ID"].max()) + 1) if not df_keluar.empty else "1"
        new_row = pd.DataFrame([[new_id, tanggal, jumlah, deskripsi]],
                               columns=["ID", "Tanggal", "Jumlah", "Deskripsi"])
        df_keluar = pd.concat([df_keluar, new_row], ignore_index=True)
        save_csv(df_keluar, FILE_PENGELUARAN)
        st.success("✅ Data pengeluaran berhasil disimpan.")

elif menu == "📋 Data Pengeluaran":
    st.header("📄 Daftar Pengeluaran")
    st.dataframe(df_keluar, use_container_width=True)

elif menu == "📊 Grafik Keuangan":
    st.header("Grafik Pemasukan & Pengeluaran")
    df_masuk["Tanggal"] = pd.to_datetime(df_masuk["Tanggal"])
    df_keluar["Tanggal"] = pd.to_datetime(df_keluar["Tanggal"])
    df_masuk["Bulan"] = df_masuk["Tanggal"].dt.to_period("M")
    df_keluar["Bulan"] = df_keluar["Tanggal"].dt.to_period("M")
    pemasukan = df_masuk.groupby("Bulan")["Jumlah"].sum()
    pengeluaran = df_keluar.groupby("Bulan")["Jumlah"].sum()
    gabung = pd.DataFrame({"Pemasukan": pemasukan, "Pengeluaran": pengeluaran}).fillna(0)
    st.bar_chart(gabung, use_container_width=True)

elif menu == "📤 Export Excel":
    st.header("Export Semua Data ke Excel")
    with pd.ExcelWriter("laporan_kas_rt.xlsx") as writer:
        df_warga.to_excel(writer, sheet_name="Warga", index=False)
        df_masuk.to_excel(writer, sheet_name="Iuran", index=False)
        df_keluar.to_excel(writer, sheet_name="Pengeluaran", index=False)
    with open("laporan_kas_rt.xlsx", "rb") as f:
        st.download_button("📥 Unduh File Excel", f, file_name="laporan_kas_rt.xlsx")

elif menu == "📑 Laporan Status Iuran":
    st.header("Status Pembayaran Iuran per Warga")
    bulan = st.selectbox("Pilih Bulan", list(calendar.month_name)[1:], index=datetime.today().month - 1)
    tahun = st.selectbox("Pilih Tahun", list(range(2020, datetime.today().year + 1)), index=5)
    bulan_num = list(calendar.month_name).index(bulan)
    df_masuk["Tanggal"] = pd.to_datetime(df_masuk["Tanggal"])
    df_filter = df_masuk[(df_masuk["Tanggal"].dt.month == bulan_num) & (df_masuk["Tanggal"].dt.year == tahun)]

    def status(nama, kategori):
        if not df_filter[(df_filter["Nama"] == nama) & (df_filter["Kategori"] == "Iuran Pokok+Kas Gang")].empty:
            return "Lunas"
        bayar = df_filter[(df_filter["Nama"] == nama) & (df_filter["Kategori"] == kategori)]
        return "Lunas" if not bayar.empty else "Belum Lunas"

    kategori_list = ["Iuran Pokok", "Iuran Kas Gang"]
    laporan = pd.DataFrame({"Nama": df_warga["Nama"]})
    for kategori in kategori_list:
        laporan[kategori] = laporan["Nama"].apply(lambda n: status(n, kategori))
    st.dataframe(laporan, use_container_width=True)
