# Tugas Kelompok MVD
# Anggota Kelompok:
# 1. Istiqaamah Hamiidah (L0225024)
# 2. Medina Amry Safarida (L0225038)
# 3. Noverla Caesarlia Mullatwati (L0225054)

# ============================================================
# 1. IMPORT LIBRARY
# Library yang digunakan untuk membaca data dan membuat dashboard
# ============================================================
import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# 2. KONFIGURASI HALAMAN
# Mengatur judul tab browser dan tampilan dashboard
# ============================================================
st.set_page_config(
    page_title="Dashboard Penjualan Kopi",
    page_icon="☕",
    layout="wide"
)

# ============================================================
# 3. MEMBACA DATASET
# Pastikan file CSV berada dalam folder yang sama dengan app.py
# Dataset menggunakan pemisah titik koma (;)
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv(
        "IstiqaamahMedinaNoverla_L0225024_L0225038_L0225054.csv",
        sep=";"
    )

    # Menghapus spasi berlebih pada nama kolom
    df.columns = df.columns.str.strip()

    # Mengubah kolom tanggal menjadi format tanggal
    df["date"] = pd.to_datetime(
        df["date"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    # Mengubah kolom waktu transaksi menjadi format tanggal-waktu
    df["datetime"] = pd.to_datetime(
        df["datetime"],
        format="%d/%m/%Y %H:%M",
        errors="coerce"
    )

    # Membersihkan kolom uang agar dapat dihitung secara numerik
    # Contoh: "Rp387,00" menjadi 387.00
    df["money"] = (
        df["money"]
        .astype(str)
        .str.strip()
        .str.replace("Rp", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
    )

    df["money"] = pd.to_numeric(
        df["money"],
        errors="coerce"
    )

    # Membersihkan spasi pada kolom kategori
    for kolom in ["cash_type", "coffee_name", "card"]:
        df[kolom] = df[kolom].astype("string").str.strip()

    # Menghapus baris yang tidak memiliki data penting
    df = df.dropna(
        subset=["date", "money", "coffee_name", "cash_type"]
    )

    # Menambahkan kolom bulan untuk analisis tren penjualan
    df["bulan"] = df["date"].dt.to_period("M").astype(str)

    return df


df = load_data()

# ============================================================
# 4. JUDUL DAN DESKRIPSI DASHBOARD
# ============================================================
st.title("☕ Dashboard Analisis Penjualan Kopi")

st.write(
    "Dashboard ini digunakan untuk menganalisis transaksi "
    "penjualan kopi berdasarkan tanggal, jenis kopi, metode "
    "pembayaran, pendapatan, dan jumlah transaksi."
)

st.caption(
    "Sumber data: Dataset transaksi penjualan kopi"
)

# ============================================================
# 5. FILTER INTERAKTIF
# Filter akan memengaruhi KPI dan seluruh grafik di bawahnya
# ============================================================
st.sidebar.header("Filter Data")

# Filter berdasarkan rentang tanggal
tanggal_min = df["date"].min().date()
tanggal_max = df["date"].max().date()

rentang_tanggal = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=(tanggal_min, tanggal_max),
    min_value=tanggal_min,
    max_value=tanggal_max
)

# Filter berdasarkan jenis kopi
daftar_kopi = sorted(df["coffee_name"].dropna().unique())

pilihan_kopi = st.sidebar.multiselect(
    "Pilih Jenis Kopi",
    options=daftar_kopi,
    default=daftar_kopi
)

# Filter berdasarkan metode pembayaran
daftar_pembayaran = sorted(
    df["cash_type"].dropna().unique()
)

pilihan_pembayaran = st.sidebar.multiselect(
    "Pilih Metode Pembayaran",
    options=daftar_pembayaran,
    default=daftar_pembayaran
)

# Memastikan rentang tanggal memiliki tanggal awal dan akhir
if isinstance(rentang_tanggal, (tuple, list)) and len(rentang_tanggal) == 2:
    tanggal_awal, tanggal_akhir = rentang_tanggal

    # Menyaring data sesuai pilihan pengguna
    data = df[
        (df["date"].dt.date >= tanggal_awal) &
        (df["date"].dt.date <= tanggal_akhir) &
        (df["coffee_name"].isin(pilihan_kopi)) &
        (df["cash_type"].isin(pilihan_pembayaran))
    ].copy()
else:
    data = df.iloc[0:0].copy()

# ============================================================
# 6. KPI (INDIKATOR UTAMA)
# Minimal 3 KPI sesuai ketentuan tugas
# ============================================================
st.subheader("Indikator Utama")

total_transaksi = len(data)
total_pendapatan = data["money"].sum()
rata_rata_transaksi = (
    data["money"].mean() if not data.empty else 0
)

if not data.empty:
    kopi_terlaris = data["coffee_name"].value_counts().idxmax()
else:
    kopi_terlaris = "-"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Total Transaksi",
    f"{total_transaksi:,}"
)

kpi2.metric(
    "Total Pendapatan",
    f"Rp{total_pendapatan:,.2f}"
)

kpi3.metric(
    "Rata-rata Nilai Transaksi",
    f"Rp{rata_rata_transaksi:,.2f}"
)

kpi4.metric(
    "Kopi Paling Banyak Terjual",
    kopi_terlaris
)

st.divider()

# ============================================================
# 7. MEMERIKSA DATA HASIL FILTER
# Jika tidak ada data, grafik tidak perlu dibuat
# ============================================================
if data.empty:
    st.warning(
        "Tidak ada data yang sesuai dengan filter. "
        "Silakan ubah pilihan tanggal, jenis kopi, "
        "atau metode pembayaran."
    )

else:
    # ========================================================
    # 8. GRAFIK 1: BAR CHART
    # Menampilkan jumlah transaksi setiap jenis kopi
    # ========================================================
    st.subheader("1. Jumlah Transaksi Berdasarkan Jenis Kopi")

    transaksi_kopi = (
        data.groupby("coffee_name")
        .size()
        .reset_index(name="jumlah_transaksi")
        .sort_values("jumlah_transaksi", ascending=False)
    )

    fig_bar = px.bar(
        transaksi_kopi,
        x="coffee_name",
        y="jumlah_transaksi",
        color="coffee_name",
        title="Jumlah Transaksi per Jenis Kopi",
        labels={
            "coffee_name": "Jenis Kopi",
            "jumlah_transaksi": "Jumlah Transaksi"
        }
    )

    st.plotly_chart(fig_bar, use_container_width=True)

    # ========================================================
    # 9. GRAFIK 2: LINE CHART
    # Menampilkan perubahan pendapatan dari waktu ke waktu
    # ========================================================
    st.subheader("2. Tren Pendapatan Bulanan")

    pendapatan_bulanan = (
        data.groupby("bulan", as_index=False)["money"]
        .sum()
        .sort_values("bulan")
    )

    fig_line = px.line(
        pendapatan_bulanan,
        x="bulan",
        y="money",
        markers=True,
        title="Tren Total Pendapatan per Bulan",
        labels={
            "bulan": "Bulan",
            "money": "Pendapatan"
        }
    )

    st.plotly_chart(fig_line, use_container_width=True)

    # ========================================================
    # 10. GRAFIK 3: PIE CHART
    # Menampilkan proporsi transaksi berdasarkan pembayaran
    # ========================================================
    st.subheader("3. Proporsi Metode Pembayaran")

    pembayaran = (
        data.groupby("cash_type")
        .size()
        .reset_index(name="jumlah_transaksi")
    )

    fig_pie = px.pie(
        pembayaran,
        names="cash_type",
        values="jumlah_transaksi",
        title="Persentase Transaksi Berdasarkan Pembayaran",
        hole=0.35
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    # ========================================================
    # 11. GRAFIK 4: HISTOGRAM
    # Menampilkan distribusi nilai transaksi
    # ========================================================
    st.subheader("4. Distribusi Nilai Transaksi")

    fig_hist = px.histogram(
        data,
        x="money",
        nbins=20,
        title="Distribusi Nominal Transaksi",
        labels={
            "money": "Nilai Transaksi",
            "count": "Jumlah Transaksi"
        }
    )

    st.plotly_chart(fig_hist, use_container_width=True)

    # ========================================================
    # 12. TABEL DATA
    # Menampilkan data setelah filter diterapkan
    # ========================================================
    st.subheader("Data Transaksi yang Ditampilkan")

    st.dataframe(
        data[
            ["date", "datetime", "cash_type",
             "money", "coffee_name"]
        ].sort_values("datetime", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # ========================================================
    # 13. UNDUH DATA HASIL FILTER
    # Memudahkan pengguna menyimpan data yang sudah disaring
    # ========================================================
    csv_hasil = data.to_csv(
        index=False,
        sep=";"
    ).encode("utf-8-sig")

    st.download_button(
        label="Unduh Data Hasil Filter",
        data=csv_hasil,
        file_name="data_transaksi_terfilter.csv",
        mime="text/csv"
    )

# ============================================================
# 14. CATATAN KAKI DASHBOARD
# ============================================================
st.caption(
    "Dashboard dibuat menggunakan Python, Pandas, "
    "Plotly, dan Streamlit."
)
