
Docker Komutları:
<pre>
// Image'leri görme
docker images

// Çalışan Container'ları görme
docker ps

// Image build etme
docker build --tag dockerhub_kullanici_adi/image_adi .

// Container olarak çalıştırma
docker run --publish 80:80 -d dockerhub_kullanici_adi/image_adi

// Container durdurma
docker stop container_adi

// Dockerhub'a image yükleme
docker push dockerhub_kullanici_adi/image_adi

// Dockerhub'dan image indirme
docker pull dockerhub_kullanici_adi/image_adi
</pre>

AWS Instance Komutları

<pre>
// Instance'ı güncelleme
sudo yum install

// Instance'a docker yüklemek
sudo yum install docker

// Instance'ta docker'ı çalıştırmak
sudo service docker start
</pre>
