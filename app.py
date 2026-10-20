# Tugas Kelompok MVD
# Anggota Kelompok:
# 1. Istiqaamah Hamiidah (L0225024)
# 2. Medina Amry Safarida (L0225038)
# 3. Noverla Caesarlia Mullatwati (L0225054)





# ============================================================
# 1. IMPORT LIBRARY
# ============================================================
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ============================================================
# 2. KONFIGURASI DASHBOARD
# ============================================================
st.set_page_config(
    page_title="Dashboard Analisis Penjualan Kopi",
    page_icon="☕",
    layout="wide"
)

# ============================================================
# 3. MEMBACA DATASET
# Pastikan CSV berada satu folder dengan app.py
# ============================================================
NAMA_FILE = "IstiqaamahMedinaNoverla_L0225024_L0225038_L0225054.csv"


@st.cache_data
def load_data():
    lokasi_file = Path(__file__).parent / NAMA_FILE

    if not lokasi_file.exists():
        raise FileNotFoundError(
            f"File {NAMA_FILE} tidak ditemukan. "
            "Pastikan file CSV berada satu folder dengan app.py."
        )

    # Mendeteksi pemisah CSV secara otomatis
    # agar koma atau titik koma tidak salah dibaca
    df = pd.read_csv(
        lokasi_file,
        sep=None,
        engine="python",
        encoding="utf-8-sig"
    )

    # Membersihkan nama kolom tanpa menghapus baris
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.strip()
    )

    # Menyimpan jumlah baris sebelum pembersihan
    jumlah_awal = len(df)

    # Memastikan kolom yang dibutuhkan tersedia
    kolom_wajib = [
        "date", "datetime", "cash_type",
        "money", "coffee_name"
    ]

    kolom_hilang = [
        kolom for kolom in kolom_wajib
        if kolom not in df.columns
    ]

    if kolom_hilang:
        raise ValueError(
            f"Kolom tidak ditemukan: {kolom_hilang}. "
            f"Kolom yang terbaca: {df.columns.tolist()}. "
            "Periksa pemisah dan struktur file CSV."
        )

    # Mengubah tanggal, tetapi mempertahankan tanggal yang kosong
    df["date"] = pd.to_datetime(
        df["date"],
        dayfirst=True,
        errors="coerce"
    )

    df["datetime"] = pd.to_datetime(
        df["datetime"],
        dayfirst=True,
        errors="coerce"
    )

    # Mengubah nilai uang menjadi angka
    def konversi_uang(nilai):
        if pd.isna(nilai):
            return float("nan")

        teks = str(nilai).strip()
        teks = teks.replace("Rp", "").replace(" ", "")

        if teks == "":
            return float("nan")

        # Contoh format 1.234,50 menjadi 1234.50
        if "," in teks and "." in teks:
            teks = teks.replace(".", "")
            teks = teks.replace(",", ".")

        # Contoh format 387,00 menjadi 387.00
        elif "," in teks:
            teks = teks.replace(",", ".")

        return pd.to_numeric(teks, errors="coerce")

    df["money"] = df["money"].apply(konversi_uang)

    # Membersihkan teks kategori tanpa menghapus baris
    for kolom in ["cash_type", "coffee_name"]:
        df[kolom] = (
            df[kolom]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    # Kolom bantu untuk filter kategori
    # Nilai kosong diberi label agar tetap bisa ditampilkan
    df["jenis_kopi_filter"] = (
        df["coffee_name"].fillna("Tidak diketahui")
    )

    df["pembayaran_filter"] = (
        df["cash_type"].fillna("Tidak diketahui")
    )

    # Kolom bulan untuk grafik tren
    df["bulan"] = df["date"].dt.strftime("%Y-%m")

    # Memastikan proses pembersihan tidak mengurangi baris
    assert len(df) == jumlah_awal

    return df, jumlah_awal


try:
    df, jumlah_data_asli = load_data()
except Exception as error:
    st.error(f"Dataset gagal dibaca: {error}")
    st.stop()

# ============================================================
# 4. JUDUL DAN DESKRIPSI
# ============================================================
st.title("☕ Dashboard Analisis Penjualan Kopi")

st.write(
    "Dashboard ini menyajikan analisis penjualan kopi "
    "berdasarkan periode waktu, jenis kopi, metode pembayaran, "
    "dan nilai transaksi."
)

st.caption("Sumber: Dataset transaksi penjualan kopi")

st.info(
    f"Jumlah data yang terbaca: {jumlah_data_asli:,} baris. "
    "Pembersihan data tidak menghapus transaksi."
)

# Peringatan jika file yang terbaca kurang dari 1.000 baris
if jumlah_data_asli < 1000:
    st.error(
        f"File CSV yang terbaca hanya memiliki "
        f"{jumlah_data_asli:,} baris. "
        "Periksa apakah file yang digunakan merupakan dataset "
        "lengkap minimal 1.000 baris. Kode ini tidak membuat "
        "transaksi palsu untuk memenuhi jumlah baris."
    )

# ============================================================
# 5. FILTER INTERAKTIF
# Tidak ada filter ID kartu atau nomor kartu
# ============================================================
st.sidebar.header("Filter Dashboard")

# Filter jenis kopi
daftar_kopi = sorted(
    df["jenis_kopi_filter"].unique().tolist()
)

pilihan_kopi = st.sidebar.multiselect(
    "Pilih Jenis Kopi",
    options=daftar_kopi,
    default=daftar_kopi
)

# Filter metode pembayaran
daftar_pembayaran = sorted(
    df["pembayaran_filter"].unique().tolist()
)

pilihan_pembayaran = st.sidebar.multiselect(
    "Pilih Metode Pembayaran",
    options=daftar_pembayaran,
    default=daftar_pembayaran
)

# Filter tanggal
st.sidebar.subheader("Filter Rentang Tanggal")

gunakan_filter_tanggal = st.sidebar.checkbox(
    "Aktifkan filter tanggal",
    value=False
)

tanggal_awal = None
tanggal_akhir = None

tanggal_valid = df["date"].dropna()

if gunakan_filter_tanggal:
    if tanggal_valid.empty:
        st.sidebar.warning(
            "Dataset tidak memiliki tanggal yang valid."
        )
    else:
        tanggal_min = tanggal_valid.min().date()
        tanggal_max = tanggal_valid.max().date()

        hasil_tanggal = st.sidebar.date_input(
            "Pilih rentang tanggal",
            value=(tanggal_min, tanggal_max),
            min_value=tanggal_min,
            max_value=tanggal_max
        )

        # Menangani kondisi satu atau dua tanggal
        if isinstance(hasil_tanggal, (tuple, list)):
            if len(hasil_tanggal) == 2:
                tanggal_awal, tanggal_akhir = hasil_tanggal
            elif len(hasil_tanggal) == 1:
                tanggal_awal = hasil_tanggal[0]
                tanggal_akhir = hasil_tanggal[0]
        else:
            tanggal_awal = hasil_tanggal
            tanggal_akhir = hasil_tanggal

# ============================================================
# 6. MENERAPKAN FILTER
# Data asli df tidak dihapus
# ============================================================
data = df[
    df["jenis_kopi_filter"].isin(pilihan_kopi)
    & df["pembayaran_filter"].isin(pilihan_pembayaran)
].copy()

if (
    gunakan_filter_tanggal
    and tanggal_awal is not None
    and tanggal_akhir is not None
):
    if tanggal_awal > tanggal_akhir:
        tanggal_awal, tanggal_akhir = (
            tanggal_akhir, tanggal_awal
        )

    tanggal_baris = data["date"].dt.date

    # Tanggal kosong tetap dipertahankan karena tanggalnya
    # tidak bisa dipastikan berada di luar rentang pilihan
    data = data[
        data["date"].isna()
        | (
            (tanggal_baris >= tanggal_awal)
            & (tanggal_baris <= tanggal_akhir)
        )
    ].copy()

st.caption(
    f"Data sesuai filter: {len(data):,} baris dari "
    f"{jumlah_data_asli:,} baris data asli."
)

# ============================================================
# 7. KPI / INDIKATOR UTAMA
# ============================================================
st.subheader("Indikator Utama")

total_transaksi = len(data)
total_pendapatan = data["money"].sum()
rata_rata_transaksi = data["money"].mean()

if not data.empty:
    frekuensi_kopi = data["jenis_kopi_filter"].value_counts()
    kopi_terlaris = frekuensi_kopi.index[0]
else:
    kopi_terlaris = "-"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Jumlah Transaksi",
    f"{total_transaksi:,}"
)

kpi2.metric(
    "Total Pendapatan",
    f"Rp{total_pendapatan:,.2f}"
)

kpi3.metric(
    "Rata-rata Transaksi",
    f"Rp{rata_rata_transaksi:,.2f}"
    if pd.notna(rata_rata_transaksi) else "-"
)

kpi4.metric(
    "Jenis Kopi Terlaris",
    kopi_terlaris
)

st.divider()

# ============================================================
# 8. VISUALISASI
# Minimal 4 jenis grafik berbeda
# ============================================================
if data.empty:
    st.warning(
        "Tidak ada data sesuai filter. "
        "Silakan pilih kategori yang lain."
    )

else:
    # --------------------------------------------------------
    # CHART 1: BAR CHART
    # Jumlah transaksi per jenis kopi
    # --------------------------------------------------------
    st.subheader("1. Jumlah Transaksi per Jenis Kopi")

    grafik_bar = (
        data.groupby("jenis_kopi_filter")
        .size()
        .reset_index(name="jumlah_transaksi")
        .sort_values("jumlah_transaksi", ascending=False)
    )

    fig_bar = px.bar(
        grafik_bar,
        x="jenis_kopi_filter",
        y="jumlah_transaksi",
        title="Jumlah Transaksi Berdasarkan Jenis Kopi",
        labels={
            "jenis_kopi_filter": "Jenis Kopi",
            "jumlah_transaksi": "Jumlah Transaksi"
        }
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # --------------------------------------------------------
    # CHART 2: LINE CHART
    # Tren pendapatan bulanan
    # --------------------------------------------------------
    st.subheader("2. Tren Pendapatan Bulanan")

    data_bulanan = data.dropna(
        subset=["bulan", "money"]
    )

    grafik_line = (
        data_bulanan.groupby("bulan")["money"]
        .sum()
        .reset_index()
        .sort_values("bulan")
    )

    if not grafik_line.empty:
        fig_line = px.line(
            grafik_line,
            x="bulan",
            y="money",
            markers=True,
            title="Tren Pendapatan per Bulan",
            labels={
                "bulan": "Bulan",
                "money": "Pendapatan"
            }
        )

        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Belum ada data valid untuk grafik tren.")

    # --------------------------------------------------------
    # CHART 3: PIE CHART
    # Proporsi metode pembayaran
    # --------------------------------------------------------
    st.subheader("3. Proporsi Metode Pembayaran")

    grafik_pie = (
        data.groupby("pembayaran_filter")
        .size()
        .reset_index(name="jumlah_transaksi")
    )

    fig_pie = px.pie(
        grafik_pie,
        names="pembayaran_filter",
        values="jumlah_transaksi",
        title="Transaksi Berdasarkan Metode Pembayaran",
        hole=0.35
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    # --------------------------------------------------------
    # CHART 4: HISTOGRAM
    # Distribusi nilai transaksi
    # --------------------------------------------------------
    st.subheader("4. Distribusi Nilai Transaksi")

    data_hist = data.dropna(subset=["money"])

    if not data_hist.empty:
        fig_hist = px.histogram(
            data_hist,
            x="money",
            nbins=20,
            title="Distribusi Nilai Transaksi",
            labels={
                "money": "Nilai Transaksi",
                "count": "Jumlah Transaksi"
            }
        )

        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Belum ada nilai transaksi yang valid.")

# ============================================================
# 9. TABEL TRANSAKSI
# Tidak menyediakan filter ID kartu atau nomor kartu
# ============================================================
st.subheader("Tabel Data Transaksi")

kolom_tabel = [
    "date", "datetime", "cash_type",
    "money", "coffee_name"
]

st.dataframe(
    data[kolom_tabel],
    use_container_width=True,
    hide_index=True,
    height=450
)

# ============================================================
# 10. DOWNLOAD DATA HASIL FILTER
# ============================================================
csv_hasil = data.to_csv(
    index=False,
    sep=";"
).encode("utf-8-sig")

st.download_button(
    label="Unduh Data Hasil Filter",
    data=csv_hasil,
    file_name="data_transaksi_kopi.csv",
    mime="text/csv"
)

# ============================================================
# 11. INFORMASI KUALITAS DATA
# ============================================================
with st.expander("Lihat Informasi Kualitas Data"):
    st.write(f"Jumlah baris asli: {len(df):,}")
    st.write(f"Jumlah baris hasil filter: {len(data):,}")
    st.write(f"Jumlah kolom asli: {len(df.columns)}")

    st.write("Jumlah nilai kosong per kolom:")

    st.dataframe(
        df.isna().sum().rename("Jumlah Nilai Kosong"),
        use_container_width=True
    )

    st.write(
        "Pembersihan dilakukan dengan mengubah format tanggal, "
        "nominal uang, dan teks kategori. Baris yang memiliki "
        "nilai kosong tidak dihapus dari dataset."
    )

# ============================================================
# 12. PENUTUP
# ============================================================
st.caption(
    "Dashboard dibuat menggunakan Python, Pandas, "
    "Plotly, dan Streamlit."
)
