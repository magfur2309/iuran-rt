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
# --- Tambah Iuran ---
if menu == "Tambah Iuran" and role == "admin":
    st.title("➕ Tambah Iuran")
    nama = st.selectbox("Nama Warga", df_warga["Nama"])
    tanggal = st.date_input("Tanggal", datetime.today())
    kategori = st.selectbox("Kategori Iuran", ["Iuran Pokok", "Iuran Kas Gang", "Iuran Pokok+Kas Gang"])

    if kategori == "Iuran Pokok":
        jumlah = 35000
    elif kategori == "Iuran Kas Gang":
        jumlah = 15000
    else:
        jumlah = 50000

    if st.button("Simpan Iuran"):
        new_id = len(df_iuran) + 1
        new_row = {
            "ID": new_id,
            "Nama": nama,
            "Tanggal": tanggal,
            "Jumlah": jumlah,
            "Kategori": kategori
        }
        df_iuran = pd.concat([df_iuran, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(df_iuran, FILE_IURAN)
        st.success("✅ Data iuran berhasil disimpan!")

# --- Lihat Iuran ---
if menu == "Lihat Iuran" and role == "admin":
    st.title("📂 Data Iuran Masuk")
    st.dataframe(df_iuran.sort_values("Tanggal", ascending=False), use_container_width=True)

# --- Halaman Konten Utama ---
if menu == "Tambah Pengeluaran" and role == "admin":
    st.title("➖ Tambah Pengeluaran")
    tanggal = st.date_input("Tanggal", datetime.today())
    jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
    deskripsi = st.text_input("Deskripsi")
    if st.button("Simpan Pengeluaran"):
        new_id = df_keluar["ID"].max() + 1 if not df_keluar.empty else 1
        df_keluar.loc[len(df_keluar)] = [new_id, tanggal, jumlah, deskripsi]
        save_csv(df_keluar, FILE_PENGELUARAN)
        st.success("✅ Data pengeluaran berhasil disimpan!")

elif menu == "Lihat Pengeluaran" and role == "admin":
    st.title("📁 Data Pengeluaran")
    st.dataframe(df_keluar.sort_values("Tanggal", ascending=False), use_container_width=True)

elif menu == "Laporan Status Iuran":
    st.title("📝 Laporan Status Iuran")
    df_iuran["Bulan"] = pd.to_datetime(df_iuran["Tanggal"]).dt.to_period("M")
    bulan_terakhir = df_iuran["Bulan"].max()
    laporan = []
    for _, row in df_warga.iterrows():
        warga = row["Nama"]
        bayar = df_iuran[(df_iuran["Nama"] == warga) & (df_iuran["Bulan"] == bulan_terakhir)]
        status = "Lunas" if not bayar.empty else "Belum Lunas"
        laporan.append({"Nama": warga, "Bulan": str(bulan_terakhir), "Status": status})
    st.dataframe(pd.DataFrame(laporan), use_container_width=True)
