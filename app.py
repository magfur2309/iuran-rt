# kas_rt_app.py
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

def backup_csv(df, file_path):
    backup_folder = "backup"
    os.makedirs(backup_folder, exist_ok=True)
    base = os.path.basename(file_path).replace(".csv", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_folder, f"{base}_backup_{timestamp}.csv")
    df.to_csv(backup_file, index=False)

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
    st.set_page_config(page_title="Iuran Kas RT", layout="centered")

    st.markdown("""
        <style>
        body {
            background-color: #0f172a;
        }
        .stApp {
            background-color: #0f172a;
            color: white;
        }
        .login-box {
            background-color: #1e293b;
            padding: 2rem;
            border-radius: 12px;
            width: 100%;
            max-width: 400px;
            margin: 5rem auto;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .login-title {
            text-align: center;
            margin-bottom: 1rem;
        }
        .login-title h1 {
            font-size: 1.6rem;
            color: white;
        }
        </style>
        <div class="login-box">
            <div class="login-title">
                <h1>🔐 Login Iuran Kas RT</h1>
            </div>
    """, unsafe_allow_html=True)

    username = st.text_input("👤 Username")
    password = st.text_input("🔒 Password", type="password")
    login_clicked = st.button("🔓 Login")

    if login_clicked:
        if username in users and password == users[username]['password']:
            st.session_state.login = True
            st.session_state.username = username
            st.session_state.role = users[username]['role']
            st.rerun()
        else:
            st.error("❌ Username atau password salah.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<div style='padding:10px; background:#1f2937; color:white; border-radius:10px;'>👤 <b>Login sebagai:</b><br>{st.session_state.username} ({st.session_state.role})</div>", unsafe_allow_html=True)
    st.markdown("---")
    role = st.session_state.role
    menu = st.radio("📋 Menu", [
        "Dashboard", "Tambah Iuran", "Lihat Iuran", 
        "Tambah Pengeluaran", "Lihat Pengeluaran",
        "Laporan Status Iuran", "Export Excel"
    ] if role == 'admin' else ["Dashboard", "Laporan Status Iuran"])
    st.markdown("---")
    if st.button("🚪 Logout"):
        st.session_state.login = False
        st.session_state.username = ''
        st.session_state.role = ''
        st.rerun()

# --- Dashboard ---
if menu == "Dashboard":
    st.title("📊 Dashboard Keuangan RT")
    if not df_iuran.empty:
        df_iuran["Tanggal"] = pd.to_datetime(df_iuran["Tanggal"])
        df_iuran["Bulan"] = df_iuran["Tanggal"].dt.to_period("M").astype(str)
    if not df_keluar.empty:
        df_keluar["Tanggal"] = pd.to_datetime(df_keluar["Tanggal"])
        df_keluar["Bulan"] = df_keluar["Tanggal"].dt.to_period("M").astype(str)

    total_masuk = df_iuran["Jumlah"].sum()
    total_keluar = df_keluar["Jumlah"].sum()
    saldo = total_masuk - total_keluar

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Pemasukan", f"Rp {total_masuk:,.0f}")
    col2.metric("💸 Pengeluaran", f"Rp {total_keluar:,.0f}")
    col3.metric("💼 Saldo", f"Rp {saldo:,.0f}")

    masuk_bulanan = df_iuran.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pemasukan")
    keluar_bulanan = df_keluar.groupby("Bulan")["Jumlah"].sum().reset_index(name="Pengeluaran")
    df_grafik = pd.merge(masuk_bulanan, keluar_bulanan, on="Bulan", how="outer").fillna(0).melt(
        id_vars=["Bulan"], var_name="Tipe", value_name="Jumlah")

    bar = alt.Chart(df_grafik).mark_bar(opacity=0.7).encode(
        x="Bulan:O", y="Jumlah:Q", color=alt.Color("Tipe:N", scale=alt.Scale(range=["#4CAF50", "#F44336"])),
        tooltip=["Bulan", "Tipe", "Jumlah"]
    )
    line = alt.Chart(df_grafik).mark_line(point=True).encode(
        x="Bulan:O", y="Jumlah:Q", color="Tipe:N"
    )
    st.altair_chart((bar + line).properties(title="📈 Grafik Kas Per Bulan"), use_container_width=True)

# --- Tambah Iuran ---
if menu == "Tambah Iuran" and role == "admin":
    st.title("➕ Tambah Iuran")
    nama = st.selectbox("Nama Warga", df_warga["Nama"])
    tanggal = st.date_input("Tanggal", datetime.today())
    kategori = st.selectbox("Kategori Iuran", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"])
    jumlah = {"Iuran Pokok": 35000, "Iuran Kas Gang": 15000, "Iuran Pokok+Kas Gang": 50000}[kategori]
    if st.button("Simpan Iuran"):
        new_id = df_iuran["ID"].max() + 1 if not df_iuran.empty else 1
        new_row = {"ID": new_id, "Nama": nama, "Tanggal": tanggal, "Jumlah": jumlah, "Kategori": kategori}
        df_iuran = pd.concat([df_iuran, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(df_iuran, FILE_IURAN)
        backup_csv(df_iuran, FILE_IURAN)
        st.success("✅ Data iuran berhasil disimpan!")

# --- Lihat Iuran (Edit & Delete) ---
if menu == "Lihat Iuran" and role == "admin":
    st.title("📂 Data Iuran Masuk")
    if not df_iuran.empty:
        selected = st.selectbox("Pilih untuk edit/hapus", df_iuran["ID"].astype(str) + " - " + df_iuran["Nama"])
        selected_id = int(selected.split(" - ")[0])
        row = df_iuran[df_iuran["ID"] == selected_id].iloc[0]
        nama = st.selectbox("Nama", df_warga["Nama"], index=df_warga[df_warga["Nama"] == row["Nama"]].index[0])
        tanggal = st.date_input("Tanggal", pd.to_datetime(row["Tanggal"]))
        kategori = st.selectbox("Kategori", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"], index=["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"].index(row["Kategori"]))
        jumlah = {"Iuran Pokok": 35000, "Iuran Kas Gang": 15000, "Iuran Pokok+Kas Gang": 50000}[kategori]
        col1, col2 = st.columns(2)
        if col1.button("💾 Simpan"):
            df_iuran.loc[df_iuran["ID"] == selected_id, ["Nama", "Tanggal", "Jumlah", "Kategori"]] = [nama, tanggal, jumlah, kategori]
            save_csv(df_iuran, FILE_IURAN)
            backup_csv(df_iuran, FILE_IURAN)
            st.success("✅ Diupdate.")
            st.rerun()
        if col2.button("🗑️ Hapus"):
            df_iuran = df_iuran[df_iuran["ID"] != selected_id]
            save_csv(df_iuran, FILE_IURAN)
            backup_csv(df_iuran, FILE_IURAN)
            st.success("🗑️ Dihapus.")
            st.rerun()
    st.dataframe(df_iuran.sort_values("Tanggal", ascending=False), use_container_width=True)

# --- Tambah Pengeluaran ---
if menu == "Tambah Pengeluaran" and role == "admin":
    st.title("➖ Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.today())
    jumlah = st.number_input("Jumlah", min_value=0, step=1000)
    deskripsi = st.text_input("Deskripsi")
    if st.button("Simpan Pengeluaran"):
        new_id = df_keluar["ID"].max() + 1 if not df_keluar.empty else 1
        df_keluar = pd.concat([df_keluar, pd.DataFrame([{"ID": new_id, "Tanggal": tanggal, "Jumlah": jumlah, "Deskripsi": deskripsi}])], ignore_index=True)
        save_csv(df_keluar, FILE_PENGELUARAN)
        backup_csv(df_keluar, FILE_PENGELUARAN)
        st.success("✅ Data pengeluaran disimpan!")

# --- Lihat Pengeluaran (Edit & Delete) ---
if menu == "Lihat Pengeluaran" and role == "admin":
    st.title("📁 Data Pengeluaran")
    if not df_keluar.empty:
        selected = st.selectbox("Pilih untuk edit/hapus", df_keluar["ID"].astype(str) + " - " + df_keluar["Deskripsi"])
        selected_id = int(selected.split(" - ")[0])
        row = df_keluar[df_keluar["ID"] == selected_id].iloc[0]
        tanggal = st.date_input("Tanggal", pd.to_datetime(row["Tanggal"]))
        jumlah = st.number_input("Jumlah", min_value=0, step=1000, value=int(row["Jumlah"]))
        deskripsi = st.text_input("Deskripsi", value=row["Deskripsi"])
        col1, col2 = st.columns(2)
        if col1.button("💾 Simpan", key="edit_keluar"):
            df_keluar.loc[df_keluar["ID"] == selected_id, ["Tanggal", "Jumlah", "Deskripsi"]] = [tanggal, jumlah, deskripsi]
            save_csv(df_keluar, FILE_PENGELUARAN)
            backup_csv(df_keluar, FILE_PENGELUARAN)
            st.success("✅ Diupdate.")
            st.rerun()
        if col2.button("🗑️ Hapus", key="hapus_keluar"):
            df_keluar = df_keluar[df_keluar["ID"] != selected_id]
            save_csv(df_keluar, FILE_PENGELUARAN)
            backup_csv(df_keluar, FILE_PENGELUARAN)
            st.success("🗑️ Dihapus.")
            st.rerun()
    st.dataframe(df_keluar.sort_values("Tanggal", ascending=False), use_container_width=True)

# --- Laporan Status Iuran ---
if menu == "Laporan Status Iuran":
    st.title("📝 Laporan Status Iuran")
    if not df_iuran.empty:
        df_iuran["Bulan"] = pd.to_datetime(df_iuran["Tanggal"]).dt.to_period("M")
        bulan_terakhir = df_iuran["Bulan"].max()
        laporan = []
        for _, row in df_warga.iterrows():
            bayar = df_iuran[(df_iuran["Nama"] == row["Nama"]) & (df_iuran["Bulan"] == bulan_terakhir)]
            status = "Lunas" if not bayar.empty else "Belum Lunas"
            laporan.append({"Nama": row["Nama"], "Bulan": str(bulan_terakhir), "Status": status})
        df_laporan = pd.DataFrame(laporan)
        st.dataframe(df_laporan, use_container_width=True)
    else:
        st.warning("Belum ada data iuran.")

# --- Export Excel ---
if menu == "Export Excel" and role == "admin":
    st.title("⬇️ Export Data ke Excel")
    tab1, tab2 = st.tabs(["Iuran", "Pengeluaran"])
    with tab1:
        st.download_button("Download Iuran", df_iuran.to_csv(index=False), "iuran.csv", "text/csv")
    with tab2:
        st.download_button("Download Pengeluaran", df_keluar.to_csv(index=False), "pengeluaran.csv", "text/csv")
