#!/bin/bash
set -e

echo "=========================================="
echo "    KioskPi Otomatik Kurulum Başlatıcı    "
echo "=========================================="

if [ "$EUID" -ne 0 ]; then
  echo "Lütfen bu komutu root (sudo) yetkisiyle çalıştırın."
  echo "Örnek: curl -sSL https://raw.githubusercontent.com/memcos/KioskPi/main/setup.sh | sudo bash"
  exit 1
fi

TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "-> KioskPi deposu indiriliyor..."
git clone -q https://github.com/memcos/KioskPi.git
cd KioskPi

echo "-> Kurulum betiği çalıştırılıyor..."
chmod +x install.sh
./install.sh

echo "-> Geçici dosyalar temizleniyor..."
cd /
rm -rf "$TEMP_DIR"
