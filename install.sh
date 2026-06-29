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

echo "[1/7] Sistem paketleri güncelleniyor ve kuruluyor..."
apt-get update
apt-get install -y greetd labwc chromium-browser python3-flask python3-bcrypt \
    python3-evdev python3-websocket python3-requests \
    plymouth plymouth-themes

echo "[2/8] Kiosk kullanıcısı oluşturuluyor..."
if id "kiosk" &>/dev/null; then
    echo "kiosk kullanıcısı zaten mevcut."
else
    useradd -m -s /bin/bash kiosk
    usermod -aG input,video,render kiosk
fi

echo "[3/7] Dizinler oluşturuluyor ve dosyalar kopyalanıyor..."
mkdir -p /opt/kioskpi
cp -r kiosk /opt/kioskpi/
cp -r config /opt/kioskpi/
cp -r plymouth /opt/kioskpi/
chown -R root:root /opt/kioskpi
chmod -R 755 /opt/kioskpi

echo "[4/7] Admin şifresi ayarlanıyor..."
if [ -f /opt/kioskpi/admin_hash.txt ]; then
    echo "Mevcut admin şifresi bulundu, korundu."
    RANDOM_PASS="[Önceden belirlediğiniz şifreniz]"
else
    echo "Yeni geçici admin şifresi oluşturuluyor..."
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
fi

echo "[5/7] Systemd servisleri ve Greetd ayarlanıyor..."
# Chromium Debug/Kiosk başlatıcı
cat << "EOF" > /usr/local/bin/chromium-debug.sh
#!/bin/bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
/usr/bin/chromium --ozone-platform=wayland --disable-dev-shm-usage --disable-extensions --disable-component-update --disable-background-networking --disable-sync --no-first-run --kiosk --noerrdialogs --disable-infobars --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=/home/kiosk/.config/chromium-kiosk about:blank > /tmp/chromium_real.log 2>&1
EOF
chmod +x /usr/local/bin/chromium-debug.sh

# Greetd yapılandırması
mkdir -p /etc/greetd
cat << "EOF" > /etc/greetd/config.toml
[terminal]
vt = 7
[default_session]
command = "/usr/bin/labwc -S /usr/local/bin/chromium-debug.sh"
user = "kiosk"
EOF

# Kiosk App servisi
cp systemd/kiosk-app.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable greetd.service
systemctl enable kiosk-app.service
systemctl restart kiosk-app.service || true

echo "[6/7] GPU Hızlandırma ayarları (/boot/firmware/config.txt)..."
# Just to ensure V3D driver is enabled (Debian Trixie standard)
if ! grep -q "dtoverlay=vc4-kms-v3d" /boot/firmware/config.txt; then
    echo "dtoverlay=vc4-kms-v3d" >> /boot/firmware/config.txt
fi

echo "[7/7] Plymouth boot teması kuruluyor..."
mkdir -p /usr/share/plymouth/themes/kioskpi
cp -r /opt/kioskpi/plymouth/kioskpi/* /usr/share/plymouth/themes/kioskpi/
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
