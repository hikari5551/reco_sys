# 服务器端部署说明

服务器端负责保存数据集、测试集、模型，并运行 YOLO。

## 部署目录

```bash
/opt/loco-roof/server_cloud
```

## 初始化服务器

```bash
sudo bash scripts/init_server_ubuntu.sh
```

## 安装依赖

```bash
cd /opt/loco-roof/server_cloud
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置环境变量

```bash
cp .env.example .env
nano .env
```

必须修改：

```text
API_KEY=换成复杂密钥
PUBLIC_BASE_URL=http://你的公网IP
```

## 测试启动

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问：

```text
http://你的公网IP:8000/docs
```

## 后台运行

```bash
sudo cp deploy/loco-roof.service /etc/systemd/system/loco-roof.service
sudo systemctl daemon-reload
sudo systemctl enable loco-roof
sudo systemctl start loco-roof
sudo systemctl status loco-roof
```

## Nginx 代理

```bash
sudo cp deploy/nginx-loco-roof.conf /etc/nginx/sites-available/loco-roof
sudo ln -s /etc/nginx/sites-available/loco-roof /etc/nginx/sites-enabled/loco-roof
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```
