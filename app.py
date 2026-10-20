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

# ============================================================
# 2. KONFIGURASI HALAMAN DASHBOARD
# ============================================================
st.set_page_config(
    page_title="Dashboard Penjualan Kopi",
    page_icon="☕",
    layout="wide"
)

# ============================================================
# 3. MEMBACA DATASET
# Data asli tidak dihapus saat proses pembersihan
# ============================================================
NAMA_FILE = "IstiqaamahMedinaNoverla_L0225024_L0225038_L0225054.csv"

@st.cache_data
def load_data():
    # Membaca CSV dengan pemisah titik koma
    df = pd.read_csv(
        NAMA_FILE,
        sep=";",
        encoding="utf-8-sig"
    )

    # Menyimpan jumlah baris asli untuk pengecekan
    jumlah_baris_asli = len(df)

    # Membersihkan nama kolom dari BOM dan spasi
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.strip()
    )

    # Memastikan kolom wajib tersedia
    kolom_wajib = [
        "date", "datetime", "cash_type",
        "card", "money", "coffee_name"
    ]

    kolom_hilang = [
        kolom for kolom in kolom_wajib
        if kolom not in df.columns
    ]

    if kolom_hilang:
        raise ValueError(
            f"Kolom tidak ditemukan: {kolom_hilang}. "
            f"Kolom yang tersedia: {df.columns.tolist()}"
        )

    # Mengubah tanggal tanpa menghapus baris yang gagal dibaca
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

    # Mengubah nominal uang menjadi angka
    # Contoh: Rp387,00 menjadi 387.00
    def ubah_ke_angka(nilai):
        if pd.isna(nilai):
            return float("nan")

        teks = str(nilai).strip()
        teks = teks.replace("Rp", "").replace(" ", "")
        teks = teks.replace("−", "-")

        # Menghapus karakter yang bukan angka,
        # tanda minus, titik, atau koma
        teks = "".join(
            karakter for karakter in teks
            if karakter.isdigit() or karakter in ".,-"
        )

        if not teks:
            return float("nan")

        # Jika terdapat koma dan titik,
        # titik dianggap pemisah ribuan
        if "," in teks and "." in teks:
            teks = teks.replace(".", "")
            teks = teks.replace(",", ".")

        # Jika hanya terdapat koma,
        # koma dianggap tanda desimal
        elif "," in teks:
            teks = teks.replace(",", ".")

        return pd.to_numeric(teks, errors="coerce")

    df["money"] = df["money"].apply(ubah_ke_angka)

    # Membersihkan spasi kategori tanpa menghapus baris
    for kolom in ["cash_type", "card", "coffee_name"]:
        df[kolom] = (
            df[kolom]
            .astype("string")
            .str.strip()
        )

        # Menganggap teks kosong sebagai data kosong
        df[kolom] = df[kolom].replace("", pd.NA)

    # Kolom bantu khusus untuk filter dan grafik.
    # Nilai kosong tetap dipertahankan pada data asli.
    df["jenis_kopi_filter"] = (
        df["coffee_name"].fillna("Tidak diketahui")
    )

    df["pembayaran_filter"] = (
        df["cash_type"].fillna("Tidak diketahui")
    )

    df["bulan"] = df["date"].dt.strftime("%Y-%m")

    # Pastikan proses pembersihan tidak mengurangi jumlah baris
    assert len(df) == jumlah_baris_asli

    return df


df = load_data()

# ============================================================
# 4. JUDUL DAN DESKRIPSI
# ============================================================
st.title("☕ Dashboard Analisis Penjualan Kopi")

st.write(
    "Dashboard ini menyajikan analisis transaksi penjualan "
    "kopi berdasarkan periode waktu, jenis kopi, metode "
    "pembayaran, dan nilai transaksi."
)

st.caption(
    "Sumber: Dataset transaksi penjualan kopi"
)

# ============================================================
# 5. INFORMASI JUMLAH DATA
# Menampilkan jumlah data asli sebelum filter
# ============================================================
total_baris_asli = len(df)

st.info(
    f"Jumlah data asli: {total_baris_asli:,} baris. "
    "Data tidak dihapus ketika proses pembersihan dilakukan."
)

if total_baris_asli < 1000:
    st.error(
        "Jumlah data asli kurang dari 1.000 baris. "
        "Periksa kembali file CSV yang digunakan."
    )

# ============================================================
# 6. FILTER INTERAKTIF
# Default filter menampilkan semua data
# ============================================================
st.sidebar.header("Filter Dashboard")

# Filter jenis kopi
opsi_kopi = sorted(
    df["jenis_kopi_filter"].unique().tolist()
)

pilihan_kopi = st.sidebar.multiselect(
    "Pilih Jenis Kopi",
    options=opsi_kopi,
    default=opsi_kopi
)

# Filter metode pembayaran
opsi_pembayaran = sorted(
    df["pembayaran_filter"].unique().tolist()
)

pilihan_pembayaran = st.sidebar.multiselect(
    "Pilih Metode Pembayaran",
    options=opsi_pembayaran,
    default=opsi_pembayaran
)

# Filter tanggal bersifat opsional agar data default
# tetap mencakup baris dengan tanggal yang tidak terbaca
gunakan_filter_tanggal = st.sidebar.checkbox(
    "Aktifkan filter tanggal",
    value=False
)

tanggal_awal = None
tanggal_akhir = None

tanggal_valid = df["date"].dropna()

if gunakan_filter_tanggal and not tanggal_valid.empty:
    tanggal_awal, tanggal_akhir = st.sidebar.date_input(
        "Rentang tanggal",
        value=(
            tanggal_valid.min().date(),
            tanggal_valid.max().date()
        ),
        min_value=tanggal_valid.min().date(),
        max_value=tanggal_valid.max().date()
    )

# ============================================================
# 7. MENYARING DATA TANPA MENGHAPUS DATA ASLI
# ============================================================
data = df[
    df["jenis_kopi_filter"].isin(pilihan_kopi)
    & df["pembayaran_filter"].isin(pilihan_pembayaran)
].copy()

# Filter tanggal hanya digunakan jika diaktifkan
if gunakan_filter_tanggal and tanggal_awal and tanggal_akhir:
    data = data[
        data["date"].isna()
        | (
            (data["date"].dt.date >= tanggal_awal)
            & (data["date"].dt.date <= tanggal_akhir)
        )
    ].copy()

# ============================================================
# 8. KPI / INDIKATOR UTAMA
# ============================================================
st.subheader("Indikator Utama")

total_transaksi = len(data)

total_pendapatan = data["money"].sum()

rata_rata_transaksi = data["money"].mean()

if not data.empty:
    kopi_terlaris = (
        data["jenis_kopi_filter"].value_counts().idxmax()
    )
else:
    kopi_terlaris = "-"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Total Baris Transaksi",
    f"{total_transaksi:,}"
)

kpi2.metric(
    "Total Pendapatan",
    f"Rp{total_pendapatan:,.2f}"
)

kpi3.metric(
    "Rata-rata Nilai Transaksi",
    (
        f"Rp{rata_rata_transaksi:,.2f}"
        if pd.notna(rata_rata_transaksi)
        else "Belum tersedia"
    )
)

kpi4.metric(
    "Jenis Kopi Terbanyak",
    kopi_terlaris
)

st.caption(
    f"Data yang ditampilkan: {len(data):,} dari "
    f"{total_baris_asli:,} baris data asli."
)

st.divider()

# ============================================================
# 9. GRAFIK
# ============================================================
if data.empty:
    st.warning(
        "Tidak ada data sesuai filter. "
        "Pilih kembali jenis kopi atau metode pembayaran."
    )

else:
    # --------------------------------------------------------
    # GRAFIK 1: BAR CHART
    # Jumlah transaksi berdasarkan jenis kopi
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
    # GRAFIK 2: LINE CHART
    # Tren pendapatan per bulan
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
            title="Perubahan Pendapatan per Bulan",
            labels={
                "bulan": "Bulan",
                "money": "Pendapatan"
            }
        )

        st.plotly_chart(
            fig_line,
            use_container_width=True
        )
    else:
        st.info("Belum ada data tanggal dan nominal yang valid.")

    # --------------------------------------------------------
    # GRAFIK 3: PIE CHART
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
    # GRAFIK 4: HISTOGRAM
    # Distribusi nilai transaksi
    # --------------------------------------------------------
    st.subheader("4. Distribusi Nilai Transaksi")

    data_histogram = data.dropna(subset=["money"])

    if not data_histogram.empty:
        fig_hist = px.histogram(
            data_histogram,
            x="money",
            nbins=20,
            title="Distribusi Nominal Transaksi",
            labels={
                "money": "Nilai Transaksi",
                "count": "Jumlah Transaksi"
            }
        )

        st.plotly_chart(
            fig_hist,
            use_container_width=True
        )
    else:
        st.info("Tidak ada nilai transaksi yang valid untuk histogram.")

# ============================================================
# 10. TABEL DATA
# Menampilkan seluruh kolom dan baris sesuai filter
# ============================================================
st.subheader("Tabel Data Transaksi")

st.write(
    "Tabel ini menampilkan semua kolom data. "
    "Data yang memiliki nilai kosong tetap ditampilkan."
)

st.dataframe(
    data[
        ["date", "datetime", "cash_type",
         "card", "money", "coffee_name"]
    ],
    use_container_width=True,
    hide_index=True,
    height=450
)

# ============================================================
# 11. UNDUH DATA HASIL FILTER
# ============================================================
csv_hasil = data[
    ["date", "datetime", "cash_type",
     "card", "money", "coffee_name"]
].to_csv(
    index=False,
    sep=";"
).encode("utf-8-sig")

st.download_button(
    label="Unduh Data yang Ditampilkan",
    data=csv_hasil,
    file_name="data_transaksi_kopi.csv",
    mime="text/csv"
)

# ============================================================
# 12. KUALITAS DATA
# Menunjukkan masalah data tanpa menghapus baris
# ============================================================
with st.expander("Lihat Informasi Kualitas Data"):
    st.write(f"Jumlah baris data asli: {len(df):,}")
    st.write(f"Jumlah baris saat ini: {len(data):,}")
    st.write(f"Jumlah kolom: {len(df.columns)}")

    st.write("Jumlah nilai kosong pada data asli:")
    st.dataframe(
        df[
            ["date", "datetime", "cash_type",
             "card", "money", "coffee_name"]
        ].isna().sum().rename("Jumlah Kosong"),
        use_container_width=True
    )

    st.write(
        "Catatan: nilai kosong dan tanggal yang gagal dibaca "
        "tidak menyebabkan baris dihapus. Grafik hanya "
        "menggunakan nilai valid untuk perhitungan terkait."
    )

# ============================================================
# 13. PENUTUP
# ============================================================
st.caption(
    "Dashboard dibuat menggunakan Python, Pandas, "
    "Plotly, dan Streamlit."
)
