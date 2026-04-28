# ETL Pipeline - Fashion Studio Product Data

ETL (Extract, Transform, Load) pipeline sederhana untuk mengekstrak data produk dari website [Fashion Studio](https://fashion-studio.dicoding.dev/), membersihkan dan mentransformasi data, serta menyimpannya ke dalam berbagai repositori data.

## Studi Kasus

Sebagai data engineer di perusahaan retail fashion, pipeline ini digunakan untuk melakukan riset terhadap harga dan produk kompetitor (Fashion Studio) yang menjual berbagai produk fashion seperti t-shirt, pants, jacket, dan outerwear.

## Fitur

- **Extract**: Web scraping 50 halaman (1000 produk) dari Fashion Studio
- **Transform**: Pembersihan data (invalid titles, price conversion, rating extraction, dll)
- **Load**: Penyimpanan ke 3 repositori data:
  - CSV file (`products.csv`)
  - Google Sheets
  - PostgreSQL (Supabase)
- **Unit Testing**: 82 test cases dengan 91% coverage
- **Error Handling**: Penanganan kesalahan di setiap fungsi

## Struktur Proyek

```
ETL-Pipeline/
├── tests/
│   ├── __init__.py
│   ├── test_extract.py
│   ├── test_transform.py
│   └── test_load.py
├── utils/
│   ├── __init__.py
│   ├── extract.py
│   ├── transform.py
│   └── load.py
├── main.py
├── requirements.txt
├── submission.txt
├── products.csv
├── google-sheets-api.json
└── .gitignore
```

## Instalasi

1. Clone repository:
   ```bash
   git clone https://github.com/rai-pramana/ETL-Pipeline.git
   cd ETL-Pipeline
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Opsional) Konfigurasi Google Sheets & PostgreSQL di `main.py`

## Cara Menjalankan

### Menjalankan ETL Pipeline
```bash
python main.py
```

### Menjalankan Unit Test
```bash
python -m pytest tests
```

### Menjalankan Test Coverage
```bash
coverage run -m pytest tests
```

## Transformasi Data

| Kolom | Sebelum | Sesudah |
|---|---|---|
| Title | `"Unknown Product"` → dihapus | Nama produk valid |
| Price | `"$50.00"` | `800000.0` (IDR, ×Rp16.000) |
| Rating | `"Rating: ⭐ 4.5 / 5"` | `4.5` (float) |
| Colors | `"3 Colors"` | `3` (int) |
| Size | `"Size: M"` | `"M"` (string) |
| Gender | `"Gender: Men"` | `"Men"` (string) |
| Timestamp | — | Waktu ekstraksi |

## Repositori Data

- **CSV**: `products.csv`
- **Google Sheets**: [Link](https://docs.google.com/spreadsheets/d/1mD4gMKEhra1Wb9qD3pP3pyOa8evdaxL1jfRNkbv0ZpQ/edit?usp=sharing)
- **PostgreSQL**: Supabase (konfigurasi di `main.py`)

## Dependencies

- `pandas` — Manipulasi data
- `requests` — HTTP requests
- `beautifulsoup4` — Web scraping
- `google-auth` & `google-api-python-client` — Google Sheets API
- `sqlalchemy` & `psycopg2-binary` — PostgreSQL
- `pytest` & `pytest-cov` — Unit testing
