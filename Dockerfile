# Python veya env bilgisini yazmalıyız.
FROM python:3.7

# Dizindeki Dosyaları Docker'a Kopyalamak
COPY . . 

# Docker Ortamına gerekli kütüphanelerin yüklenmesi
RUN pip3 install -r "requirements.txt"

# Flask için Env Değişkenlerini Kontrol ediyoruz.
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0

# Ayağa kaldıracağımız Portu belirliyoruz (Burada yazdığımız ile Flask'ın portlarının eşleşmesi gerekiyor.)
EXPOSE 85

# Programın Ayağa Kaldırılması
CMD ["flask", "run", "--port", "85"]