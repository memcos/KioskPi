# KioskPi 🚀

[![Language](https://img.shields.io/badge/Language-Python%20%7C%20Bash-blue.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20OS%20Debian%2013-green.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Read this in other languages: [English](#english) | [Türkçe](#türkçe)*

---

## English

KioskPi is a highly optimized, Wayland (cage) based kiosk application powered by Chromium, specifically designed for Raspberry Pi 3+ devices running Raspberry Pi OS Lite Debian 13 (Trixie) 64-bit.

### ✨ Features

- **GPU Acceleration:** Hardware-accelerated smooth performance with the V3D driver support.
- **Idle Timeout Redirection:** Automatically switches to a secondary URL (e.g., an ad page or screensaver) if left inactive for a configured amount of time.
- **Barcode Scanner Support (evdev):** Listens for USB barcode scanners in the background. When a barcode is scanned, it instantly switches back to the primary URL and types the data into the target field.
- **Modern Web Dashboard:** A sleek, responsive, dark-themed admin panel accessible over the local network (`http://<pi-ip>:8080`) for easy configuration.
- **Customizable Boot Logo:** Easily change the system boot splash screen via the admin panel using Plymouth.
- **Low RAM Usage:** Uses the lightweight `cage` Wayland compositor instead of a full desktop environment.

### 🛠️ Installation

Run the installation script with root privileges. It will automatically install all dependencies, configure the `kiosk` user, and set up the `systemd` services.

```bash
chmod +x install.sh
sudo ./install.sh
```

At the end of the installation, the script will output the device's IP address and a **randomly generated admin password**.

### 💻 Usage

1. Restart the device after installation (`sudo reboot`).
2. Go to `http://<Device-IP>:8080` from another device on the same network.
3. Log in with the password provided during installation.
4. You can configure the Primary/Secondary URLs, Idle Timeout, Input Field Selectors, and update your Boot Logo via the dashboard.

### 🗑️ Uninstallation

To completely remove the kiosk application and its services:

```bash
chmod +x uninstall.sh
sudo ./uninstall.sh
```

---

## Türkçe

KioskPi, Raspberry Pi 3 ve üstü cihazlar için optimize edilmiş, Wayland (cage) ve Chromium tabanlı bir kiosk uygulamasıdır. Raspberry Pi OS Lite Debian 13 (Trixie) 64-bit üzerinde tam performanslı çalışacak şekilde tasarlanmıştır.

### ✨ Özellikler

- **GPU Hızlandırma:** V3D sürücüsü desteği ile donanım hızlandırmalı akıcı performans.
- **Otomatik Bekleme (Idle) Geçişi:** Belirlenen süre boyunca kullanılmadığında ikincil bir URL'ye (reklam vb.) geçiş yapar.
- **Barkod Okuyucu Desteği (evdev):** Arka planda USB barkod okuyucuyu dinler. Etkileşim sağlandığında otomatik olarak ana URL'ye döner ve barkod bilgisini doğrudan giriş alanına iletir.
- **Modern Yönetim Paneli:** Responsive, karanlık mod (dark-theme) arayüz ile ağ üzerinden kolay konfigürasyon (`http://<cihaz-ip>:8080`).
- **Özelleştirilebilir Boot Logosu:** Sistem açılış ekranını (Plymouth) yönetim paneli üzerinden tek tıkla değiştirebilirsiniz.
- **Düşük RAM Tüketimi:** Ağır masaüstü ortamları yerine sadece `cage` Wayland compositor kullanılır.

### 🛠️ Kurulum

Aşağıdaki komutları kullanarak sistemi tam otomatik olarak kurabilirsiniz:

```bash
chmod +x install.sh
sudo ./install.sh
```

Kurulum bittiğinde ekranda beliren IP adresi ve oluşturulan **rastgele şifre** ile yönetim paneline bağlanabilirsiniz.

### 💻 Kullanım

1. Kurulum sonrasında cihazı yeniden başlatın (`sudo reboot`).
2. Ağınızdaki başka bir cihazdan tarayıcı üzerinden `http://<Cihaz-IP-Adresi>:8080` adresine girin.
3. Kurulumda ekranda beliren rastgele şifre ile giriş yapın.
4. Birincil ve ikincil URL'leri, bekleme süresini, boot logosunu ve cihaz ayarlarını panel üzerinden kolayca yapılandırabilirsiniz.

### 🗑️ Kaldırma

Uygulamayı ve sistem servislerini tamamen sistemden kaldırmak için:

```bash
chmod +x uninstall.sh
sudo ./uninstall.sh
```

---

### 📝 Architecture / Mimari Notlar
- **Backend:** Python (Flask, evdev, websocket-client)
- **Frontend:** Vanilla HTML/CSS/JS (Admin UI), Chromium (Kiosk Engine)
- **Display Layer:** `cage` Wayland compositor
- **Service Management:** `systemd`
