Environment
-----------
Python 3.6

Dependencies
------------
Scrapy
pywin32 (kalo minta)

Usage
------
python detik_komen.py [-c] [-s] [-d] [-p]

-c jumlah komen per artikel -> default: 100 (kalo kebanyakan kadang error)
-s mulai dari halaman ke-... -> default: 1
-d delay per akses server (antisipasi biar gak di ban IP) -> default: 0
-p jumlah halaman terbaru yg di crawl -> default: 0 (semua, soalnya halaman terakhir di next lagi redirect ke /pemilu/0)

contoh:
python detik_komen.py -c 100 -s 5 -d 0.1 -p 10

ket:
-ambil 100 komen pertama per artikel
-mulai dari halaman ke-5 (https://www.detik.com/pemilu/5)
-delay 0.1 detik per akses ke API
-ambil 10 halaman ke belakang

Output
------
data.csv -> list komen, format id_berita;tgl_berita;komen;tgl_komen
history.csv -> menyimpan id komentar terakhir yg di crawl (biar data.csv bisa nambah terus tanpa kedobelan data)