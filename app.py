import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import os

# --- File Path CSV ---
FILE_WARGA = "warga.csv"
FILE_IURAN = "iuran_masuk.csv"
FILE_PENGELUARAN = "pengeluaran.csv"

# --- Fungsi Backup, Load & Save CSV ---
def backup_csv(file_path):
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"backup/{os.path.basename(file_path).replace('.csv', '')}_{timestamp}.csv"
        os.makedirs("backup", exist_ok=True)
        df_backup = pd.read_csv(file_path)
        df_backup.to_csv(backup_path, index=False)

def save_csv(df, file_path):
    backup_csv(file_path)
    df.to_csv(file_path, index=False)

def load_csv(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=columns)

def delete_row(df, row_id):
    return df[df["ID"] != row_id].reset_index(drop=True)

def edit_row(df, row_id, new_data):
    df.loc[df["ID"] == row_id, list(new_data.keys())] = list(new_data.values())
    return df

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
    st.markdown("""
        <style>
        body { background-color: #111827; }
        .stApp { background-color: #111827; color: white; }
        .login-container { margin-top: 100px; text-align: center; }
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

# --- Sidebar ---
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

    menu_options = (
        [
            ("Dashboard", "📊 Dashboard"),
            ("Tambah Iuran", "➕ Tambah Iuran"),
            ("Lihat Iuran", "📂 Lihat Iuran"),
            ("Tambah Pengeluaran", "➖ Tambah Pengeluaran"),
            ("Lihat Pengeluaran", "📁 Lihat Pengeluaran"),
            ("Laporan Status Iuran", "📝 Status Iuran"),
            ("Export Excel", "⬇️ Export Excel")
        ] if role == "admin" else [
            ("Dashboard", "📊 Dashboard"),
            ("Laporan Status Iuran", "📝 Status Iuran")
        ]
    )

    st.markdown("""
        <style>
        .menu-button {
            background-color: #1f2937;
            color: white;
            padding: 10px 16px;
            border-radius: 8px;
            border: none;
            font-weight: bold;
            width: 100%;
            text-align: left;
            margin-bottom: 5px;
        }
        .menu-button:hover {
            background-color: #374151;
        }
        .menu-selected {
            background-color: #f43f5e !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

    menu_labels = [label for _, label in menu_options]
    menu_keys = [key for key, _ in menu_options]

    for idx, label in enumerate(menu_labels):
        button_key = f"menu_{idx}"
        if st.button(label, key=button_key):
            st.session_state["selected_menu"] = menu_keys[idx]

    if "selected_menu" not in st.session_state:
        st.session_state["selected_menu"] = menu_keys[0]

    menu = st.session_state["selected_menu"]

    st.markdown("---")
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #1f2937;
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            border: none;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .stButton>button:hover {
            background-color: #374151;
        }
        </style>
    """, unsafe_allow_html=True)
    if st.button("📕 Logout"):
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
    jumlah = 35000 if kategori == "Iuran Pokok" else 15000 if kategori == "Iuran Kas Gang" else 50000
    if st.button("Simpan Iuran"):
        new_id = df_iuran["ID"].max() + 1 if not df_iuran.empty else 1
        new_row = {"ID": new_id, "Nama": nama, "Tanggal": tanggal, "Jumlah": jumlah, "Kategori": kategori}
        df_iuran = pd.concat([df_iuran, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(df_iuran, FILE_IURAN)
        st.success("✅ Data iuran berhasil disimpan!")

# --- Lihat Iuran ---
if menu == "Lihat Iuran" and role == "admin":
    st.title("📂 Data Iuran Masuk")
    if not df_iuran.empty:
        selected_id = st.selectbox("Pilih ID untuk Edit/Hapus", df_iuran["ID"])
        selected_data = df_iuran[df_iuran["ID"] == selected_id].iloc[0]
        nama_list = df_warga["Nama"].tolist()
        index_nama = next((i for i, nama in enumerate(nama_list) if nama == selected_data["Nama"]), 0)
        nama_edit = st.selectbox("Nama", nama_list, index=index_nama)
        tanggal_edit = st.date_input("Tanggal", pd.to_datetime(selected_data["Tanggal"]))
        kategori_edit = st.selectbox("Kategori", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"], index=["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"].index(selected_data["Kategori"]))
        jumlah_edit = 35000 if kategori_edit == "Iuran Pokok" else 15000 if kategori_edit == "Iuran Kas Gang" else 50000
        col1, col2 = st.columns(2)
        if col1.button("💾 Simpan Perubahan"):
            df_iuran = edit_row(df_iuran, selected_id, {"Nama": nama_edit, "Tanggal": tanggal_edit, "Kategori": kategori_edit, "Jumlah": jumlah_edit})
            save_csv(df_iuran, FILE_IURAN)
            st.success("✅ Data berhasil diperbarui!")
            st.rerun()
        if col2.button("🗑️ Hapus Data"):
            df_iuran = delete_row(df_iuran, selected_id)
            save_csv(df_iuran, FILE_IURAN)
            st.warning("⚠️ Data berhasil dihapus!")
            st.rerun()
    st.dataframe(df_iuran.sort_values("Tanggal", ascending=False), use_container_width=True)
