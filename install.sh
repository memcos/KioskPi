#!/bin/bash
set -e

echo "=========================================="
echo "      KioskPi Kurulum Sihirbazı           "
echo "=========================================="

if [ "$EUID" -ne 0 ]; then
  echo "Lütfen bu scripti root (sudo) yetkisiyle çalıştırın."
  exit 1
fi

# Detect IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo "[1/8] Sistem paketleri güncelleniyor ve kuruluyor..."
apt-get update
apt-get install -y cage chromium-browser python3-flask python3-bcrypt \
    python3-evdev python3-websocket python3-requests \
    plymouth plymouth-themes

echo "[2/8] Kiosk kullanıcısı oluşturuluyor..."
if id "kiosk" &>/dev/null; then
    echo "kiosk kullanıcısı zaten mevcut."
else
    useradd -m -s /bin/bash kiosk
    usermod -aG input,video,render kiosk
fi

echo "[3/8] Dizinler oluşturuluyor ve dosyalar kopyalanıyor..."
mkdir -p /opt/kioskpi
cp -r kiosk /opt/kioskpi/
cp -r config /opt/kioskpi/
cp -r plymouth /opt/kioskpi/
chown -R root:root /opt/kioskpi
chmod -R 755 /opt/kioskpi

echo "[4/8] Geçici admin şifresi oluşturuluyor..."
RANDOM_PASS=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 8)
# We use python to hash and set the password
python3 -c "
import bcrypt
import os
hashed = bcrypt.hashpw('${RANDOM_PASS}'.encode('utf-8'), bcrypt.gensalt())
os.makedirs('/opt/kioskpi', exist_ok=True)
with open('/opt/kioskpi/admin_hash.txt', 'wb') as f:
    f.write(hashed)
"
chmod 600 /opt/kioskpi/admin_hash.txt

echo "[5/8] Systemd servisleri ayarlanıyor..."
cp systemd/kiosk-display.service /etc/systemd/system/
cp systemd/kiosk-app.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable kiosk-display.service
systemctl enable kiosk-app.service

echo "[6/8] TTY1 Auto-login ayarlanıyor (kiosk kullanıcısı için)..."
mkdir -p /etc/systemd/system/getty@tty1.service.d/
cat > /etc/systemd/system/getty@tty1.service.d/override.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin kiosk --noclear %I \$TERM
EOF
systemctl daemon-reload

echo "[7/8] GPU Hızlandırma ayarları (/boot/firmware/config.txt)..."
# Just to ensure V3D driver is enabled (Debian Trixie standard)
if ! grep -q "dtoverlay=vc4-kms-v3d" /boot/firmware/config.txt; then
    echo "dtoverlay=vc4-kms-v3d" >> /boot/firmware/config.txt
fi

echo "[8/8] Plymouth boot teması kuruluyor..."
python3 -c "
import sys
sys.path.append('/opt/kioskpi/kiosk')
import boot_logo
boot_logo.apply_logo('/opt/kioskpi/kiosk/static/logo.png') # Varsayılan logo gerekebilir
" || echo "Boot logo şimdilik atlandı."
plymouth-set-default-theme -R kioskpi || echo "Initramfs güncellenirken uyarı, bu normal olabilir."

echo "=========================================="
echo "          KURULUM TAMAMLANDI!             "
echo "=========================================="
echo "Sistemi şimdi veya daha sonra yeniden başlatabilirsiniz."
echo ""
echo "Yönetim Paneline Erişim İçin:"
echo "Adres : http://$IP_ADDR:8080"
echo "Şifre : $RANDOM_PASS"
echo "------------------------------------------"
echo "İlk girişte bu şifreyi değiştirmeniz önerilir."
echo "=========================================="
