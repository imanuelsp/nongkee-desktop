# Nongkee untuk desktop

Klien native Python dengan Tkinter/ttk. Aplikasi membutuhkan server [Nongkee Django](https://github.com/imanuelsp/nongkee-django) yang berjalan. Akun, profil, kelas, meet, dan Friends berasal dari server tersebut.

## Menjalankan

1. Jalankan migrasi dan server sesuai README repositori Django.
2. Gunakan Python 3.12+ dengan Tkinter. Cek instalasi dengan `python -m tkinter`.
3. Dari direktori ini jalankan `python nongkee.py`. Server bawaan adalah `http://127.0.0.1:8000`. Untuk server lain, tetapkan `$env:NONGKEE_URL = "https://nama-server-anda"` di PowerShell terlebih dahulu.

Open Meets ditampilkan saat aplikasi dibuka. Gunakan navigasi kiri untuk membuka Kelas Kosong atau Friends. Masuk dengan email melalui tombol kanan atas. Pilih kartu tambah untuk membuat meet, atau buka kartu untuk bergabung. Di Kelas Kosong, pilih tanggal, waktu, area, dan ruang sebelum memilih Start a Meet. Di Friends, kirim undangan melalui @username unik atau terima undangan masuk.

## Profil dan SSO UI

Klik nama di kanan atas untuk mengubah nama tampilan, username unik, foto, kelas dan minat. Tab Kelas saya menampilkan jadwal berikutnya. Pilih rombel yang sama agar kartu di Friends menunjukkan “This person is in your class”. Tindakan **Verifikasi mahasiswa UI** terpisah dari login email. Pada rilis ini status selalu **Belum terverifikasi**. Pengelola harus memperoleh pendaftaran aplikasi, endpoint resmi, callback HTTPS, dan akses atribut status mahasiswa aktif dari UI, lalu mengimplementasikan validasi respons pada server. Rincian tersedia di README Django. Kredensial SSO dikelola di server. Klien desktop tidak menerima kata sandi SSO UI.

## Google Sign-In

Aktifkan Firebase Authentication di backend sesuai README Django. Tombol Lanjutkan dengan Google membuka browser sistem. Setelah memilih akun Google, salin kode sekali pakai kembali ke dialog desktop dalam tiga menit. Akun email lama dapat dihubungkan dahulu dari profil web. Untuk backend produksi, set NONGKEE_URL ke domain HTTPS yang sama sebelum membuka aplikasi.
