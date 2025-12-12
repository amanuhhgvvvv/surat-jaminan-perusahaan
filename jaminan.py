import streamlit as st
import datetime
import gspread
import pandas as pd
from gspread import Worksheet
from google.oauth2.service_account import Credentials

# --- KONFIGURASI GOOGLE SHEETS BARU (Untuk SJP) ---
# PASTIKAN SPREADSHEET INI SUDAH ADA DI DRIVE ANDA DAN DIBAGIKAN KE SERVICE ACCOUNT
SPREADSHEET_NAME_SJP = "PermintaanMobil dan Surat Jaminan Perusahaan"
WORKSHEET_NAME_SJP = "JAMINAN PERUSAHAAN" # Sesuaikan dengan nama sheet/tab di Google Sheet Anda

# --- KONEKSI GOOGLE SHEETS (Reuse code) ---
@st.cache_resource(ttl=3600)
def get_gspread_client():
    """Menginisialisasi koneksi gspread."""
    try:
        creds_info = {
            "type": "service_account",
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": st.secrets["client_x509_cert_url"]
        }
        credentials = Credentials.from_service_account_info(
            creds_info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Gagal menginisialisasi koneksi Google Sheets. Error: {e}")
        st.stop()

@st.cache_resource(ttl=3600)
def get_worksheet_sjp() -> Worksheet:
    """Mendapatkan objek worksheet SJP."""
    try:
        gc = get_gspread_client()
        sh = gc.open(SPREADSHEET_NAME_SJP)
        return sh.worksheet(WORKSHEET_NAME_SJP)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Error: Spreadsheet '{SPREADSHEET_NAME_SJP}' tidak ditemukan. Pastikan nama file dan izin Service Account benar.")
        st.stop()
    except Exception as e:
        st.error(f"Gagal membuka Worksheet. Error: {e}")
        st.stop()

# Panggil fungsi koneksi di awal aplikasi
ws_sjp = get_worksheet_sjp()


# 1. Konfigurasi Data Master
STATUS_CHOICES = [
    "Karyawan", "Istri", "Anak ke-1", "Anak ke-2", "Anak ke-3"
]

st.set_page_config(page_title="Surat Jaminan Perusahaan", layout="centered")

st.title("📄 Pengajuan Surat Jaminan Perusahaan (SJP)")
st.caption("Formulir ini digunakan untuk mencatat dan mengajukan data klaim jaminan.")

# Menggunakan st.form untuk menangani input dalam satu transaksi
with st.form(key='sjp_form'):
    st.header("1. Detail Pemohon/Pasien")
    
    # Bagian Detail Karyawan
    nama = st.text_input("Nama Karyawan/Pemohon:", help="Nama Karyawan yang mengajukan jaminan.")
    nik = st.text_input("NIK:", help="Nomor Induk Karyawan/Pegawai.")
    departemen = st.text_input("Departemen:")
    status = st.selectbox("Status Pasien:", options=['Pilih Status'] + STATUS_CHOICES)

    # Bagian Detail Medis
    st.header("2. Detail Medis & Perawatan")
    
    diagnosa = st.text_area("Diagnosa (ICD-10):", help="Masukkan diagnosa medis pasien secara lengkap.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tanggal_masuk = st.date_input(
            "Tanggal Masuk RS:", 
            datetime.date.today(),
        )
        
    with col2:
        tanggal_keluar = st.date_input(
            "Tanggal Keluar RS (Estimasi):", 
            datetime.date.today() + datetime.timedelta(days=1),
        )
        
    # Validasi Tambahan
    if tanggal_masuk > tanggal_keluar:
        st.warning("Tanggal Keluar RS harus setelah Tanggal Masuk RS.")
        
    # Tombol Submit
    submit_button = st.form_submit_button(label='Simpan Data Jaminan')

# 2. Logika Pemrosesan (Setelah Tombol Ditekan)
if submit_button:
    # Validasi Dasar
    if 'Pilih Status' in status or not all([nama, nik, departemen, diagnosa]):
        st.error("❌ Mohon lengkapi semua data formulir dengan benar.")
    elif tanggal_masuk > tanggal_keluar:
        st.error("❌ Tanggal Keluar RS tidak boleh sebelum Tanggal Masuk RS.")
    else:
        try:
            # --- LOGIKA PENYIMPANAN DATA KE GOOGLE SHEETS ---
            
            data_sjp = [
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                nama,
                nik,
                departemen,
                status,
                diagnosa,
                tanggal_masuk.strftime('%Y-%m-%d'),
                tanggal_keluar.strftime('%Y-%m-%d'),
            ]

            ws_sjp.append_row(data_sjp)
            
            st.success("✅ Data Surat Jaminan Perusahaan Berhasil Disimpan!")
            st.balloons()
            
            st.subheader("Ringkasan Data SJP:")
            columns_sjp = [
                "Waktu_Pengajuan", "Nama", "NIK", "Departemen", 
                "Status", "Diagnosa", "Tgl_Masuk_RS", "Tgl_Keluar_RS"
            ] 
            st.dataframe(pd.DataFrame([data_sjp], columns=columns_sjp))

        except Exception as e:
            st.error(f"Terjadi kesalahan saat menyimpan data SJP ke Google Sheets. Error: {e}")
