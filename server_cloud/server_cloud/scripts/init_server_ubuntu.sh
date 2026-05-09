#!/usr/bin/env bash
set -e

# Ubuntu 云服务器初始化脚本。
# 使用方式：sudo bash scripts/init_server_ubuntu.sh

APP_USER="app"

apt update
apt upgrade -y
timedatectl set-timezone Asia/Shanghai || true

if ! id "$APP_USER" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "$APP_USER"
  usermod -aG sudo "$APP_USER"
fi

apt install -y python3 python3-venv python3-pip nginx git sqlite3 ufw curl htop unzip ffmpeg libgl1 libglib2.0-0

# 2GB 内存服务器建议增加 2GB swap。
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

mkdir -p /opt/loco-roof/server_cloud
mkdir -p /data/loco-roof/uploads /data/loco-roof/models /data/loco-roof/results /data/loco-roof/db /data/loco-roof/logs
chown -R "$APP_USER":"$APP_USER" /opt/loco-roof /data/loco-roof

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "服务器初始化完成。"
