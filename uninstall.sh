#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Lütfen bu scripti root (sudo) yetkisiyle çalıştırın."
  exit 1
fi

echo "KioskPi kaldırılıyor..."

systemctl stop kiosk-display.service || true
systemctl stop kiosk-app.service || true
systemctl disable kiosk-display.service || true
systemctl disable kiosk-app.service || true

rm -f /etc/systemd/system/kiosk-display.service
rm -f /etc/systemd/system/kiosk-app.service
systemctl daemon-reload

rm -rf /opt/kioskpi
rm -rf /etc/systemd/system/getty@tty1.service.d/override.conf

plymouth-set-default-theme -R tribar || true

echo "Kaldırma işlemi tamamlandı."
