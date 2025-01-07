# Menggunakan image Python versi 3.9
FROM python:3.9-slim

# Menentukan direktori kerja dalam container
WORKDIR /app

# Menyalin semua file dari folder project lokal ke folder /app dalam container
COPY . /app

# Menginstall dependencies dari file requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Menentukan perintah yang dijalankan ketika container dijalankan
CMD ["python", "app.py"]

#menggunakan PORT 5000
EXPOSE 5000
