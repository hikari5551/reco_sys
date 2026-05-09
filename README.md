# 机车车顶异物识别系统（前后端交互版）

本项目是基于 **YOLOv8** 的机车车顶异物识别系统，已经由原来的“本地单机检测程序”改造为 **客户端 + 云服务器后端** 的前后端交互架构。

改造后的系统中，客户端主要负责页面展示和接口调用；云服务器负责保存数据集、测试集、模型文件、运行 YOLO 检测、保存检测结果和提供 API 接口。这样可以降低客户端环境配置难度，也更符合真实工程项目中“前端展示、后端处理、服务器存储、模型推理”的开发模式。

---

## 一、项目背景

机车车顶设备较多，结构复杂，车顶异物可能影响列车运行安全。传统人工巡检存在效率低、主观性强、结果难以结构化保存等问题。本项目利用深度学习目标检测算法，对机车车顶图片中的异物进行自动识别，并通过前后端交互程序实现图片上传、模型管理、检测推理、结果展示和数据持久化管理。

本系统适合用于：

- 机车车顶异物检测演示；
- 深度学习目标检测课程设计；
- 毕业设计 / 开题答辩项目；
- YOLOv8 工程化部署学习；
- 前后端交互和云服务器部署实践。

---

## 二、项目整体架构

改造后的系统分为两部分：

```text
loco_roof_full_frontend_backend_interactive/
├── client_interface/        # 客户端程序，只负责界面展示和接口调用
├── server_cloud/            # 云服务器后端，负责数据库、模型、图片和 YOLO 推理
└── README_前后端交互改造说明.md
```

系统运行逻辑如下：

```text
客户端 PySide6 界面
        ↓ HTTP 接口请求
云服务器 FastAPI 后端
        ↓
SQLite 数据库 + 服务器文件目录
        ↓
YOLOv8 模型推理
        ↓
返回原图 URL、检测结果图 URL、检测框数据
        ↓
客户端显示原图与检测结果
```

---

## 三、前后端职责划分

### 1. 客户端负责

客户端位于：

```text
client_interface/
```

客户端主要功能：

- 输入服务器地址和 API Key；
- 测试服务器连接；
- 创建数据集；
- 上传图片到服务器；
- 上传 `.pt` 模型到服务器；
- 刷新数据集列表、图片列表和模型列表；
- 请求服务器检测当前图片；
- 显示原图和检测结果图；
- 显示检测类别、置信度和检测框坐标；
- 查看服务器统计信息。

客户端不再负责：

- 不再保存数据集；
- 不再保存测试集；
- 不再保存 `.pt` 模型；
- 不再保留 `yolo.py`；
- 不再保留 `1_yolo.py`；
- 不再直接运行 YOLO；
- 不再依赖 `ultralytics` 进行本地推理。

也就是说，客户端现在是一个轻量化的接口访问程序，只需要安装：

```text
PySide6
requests
```

---

### 2. 云服务器后端负责

服务器端位于：

```text
server_cloud/
```

服务器端主要功能：

- 提供 FastAPI 后端接口；
- 使用 SQLite 保存结构化数据；
- 保存上传的数据集图片；
- 保存测试集图片；
- 保存上传的 `.pt` 模型；
- 运行 YOLOv8 检测；
- 保存检测后的结果图；
- 保存检测结果数据；
- 提供静态图片访问地址；
- 提供 Nginx 和 systemd 部署配置。

服务器中的数据建议保存在：

```text
/data/loco-roof/uploads      # 数据集、测试集图片
/data/loco-roof/models       # YOLO .pt 模型文件
/data/loco-roof/results      # 检测结果图
/data/loco-roof/db/app.db    # SQLite 数据库
/data/loco-roof/logs         # 日志目录
```

---

## 四、目录结构说明

### 1. 总目录结构

```text
loco_roof_full_frontend_backend_interactive/
├── client_interface/
│   ├── client/
│   │   ├── __init__.py
│   │   ├── api_client.py
│   │   ├── config.py
│   │   └── main_window.py
│   ├── main.py
│   ├── requirements.txt
│   └── README_CLIENT.md
│
├── server_cloud/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py
│   │   └── yolo_service.py
│   ├── deploy/
│   │   ├── loco-roof.service
│   │   └── nginx-loco-roof.conf
│   ├── scripts/
│   │   └── init_server_ubuntu.sh
│   ├── .env.example
│   ├── requirements.txt
│   └── README_SERVER.md
│
└── README_前后端交互改造说明.md
```

---

### 2. 客户端文件说明

```text
client_interface/main.py
```

客户端启动入口，负责创建 PySide6 应用并打开主窗口。

```text
client_interface/client/config.py
```

客户端配置文件，主要配置服务器地址和 API Key。

```python
SERVER_URL = "http://你的服务器IP:8000"
API_KEY = "服务器端 .env 中配置的 API_KEY"
```

```text
client_interface/client/api_client.py
```

客户端接口封装文件，所有 HTTP 请求都通过这个文件发送到云服务器。包括创建数据集、上传图片、上传模型、执行检测、获取统计信息等。

```text
client_interface/client/main_window.py
```

客户端主界面文件，使用 PySide6 实现。界面包含服务器配置、数据集管理、图片管理、模型管理、检测操作、原图显示、检测结果显示和日志输出等功能。

```text
client_interface/requirements.txt
```

客户端依赖文件。

---

### 3. 服务器端文件说明

```text
server_cloud/app/main.py
```

FastAPI 后端入口文件，定义了数据集、图片、模型、检测、统计等主要接口。

```text
server_cloud/app/config.py
```

服务器配置文件，负责读取环境变量，配置数据目录、数据库地址、模型目录、结果图目录等。

```text
server_cloud/app/db.py
```

数据库连接文件，默认使用 SQLite。

```text
server_cloud/app/models.py
```

数据库表结构文件，定义了数据集表、图片表、人工标注表、模型表和检测结果表。

```text
server_cloud/app/schemas.py
```

接口请求和响应数据结构文件，用于规定 API 输入输出格式。

```text
server_cloud/app/security.py
```

接口鉴权文件，使用 `X-API-Key` 对重要接口进行保护。

```text
server_cloud/app/yolo_service.py
```

YOLO 推理服务文件，负责加载 `.pt` 模型、执行检测、绘制检测框、保存检测结果图。

```text
server_cloud/deploy/loco-roof.service
```

systemd 服务配置文件，用于让后端程序在服务器后台运行，并支持开机自启。

```text
server_cloud/deploy/nginx-loco-roof.conf
```

Nginx 反向代理配置文件，用于通过公网 IP 或域名访问后端服务。

```text
server_cloud/scripts/init_server_ubuntu.sh
```

Ubuntu 云服务器初始化脚本，包含安装 Python、Nginx、SQLite、创建 swap、创建项目目录、放行端口等操作。

---

## 五、数据库设计

本项目不建议把图片、视频和 `.pt` 模型文件直接存进数据库。正确做法是：

```text
图片 / 模型文件：保存在服务器硬盘目录
数据库：只保存路径、URL、类别、坐标、置信度、时间等结构化信息
```

数据库默认使用 SQLite，文件位置为：

```text
/data/loco-roof/db/app.db
```

主要数据表如下：

### 1. datasets 数据集表

用于保存数据集基本信息。

```text
id              数据集 ID
name            数据集名称
description     数据集描述
created_at      创建时间
```

### 2. images 图片表

用于保存上传图片的信息。

```text
id              图片 ID
dataset_id      所属数据集 ID
filename        服务器保存后的文件名
original_name   原始文件名
file_path       图片在服务器上的本地路径
url             图片公网访问地址
split           数据集划分：train / val / test / unassigned
sha256          文件哈希
width           图片宽度
height          图片高度
size_bytes      文件大小
created_at      上传时间
```

### 3. annotations 人工标注表

用于保存人工标注框，后续可以扩展为训练数据导出功能。

```text
id              标注 ID
image_id        所属图片 ID
class_name      类别名称
x1              左上角 x 坐标
y1              左上角 y 坐标
x2              右下角 x 坐标
y2              右下角 y 坐标
note            备注
created_at      创建时间
```

### 4. model_files 模型表

用于保存上传到服务器的 YOLO 模型信息。

```text
id              模型 ID
name            模型名称
file_path       模型文件路径
active          是否为当前启用模型
created_at      上传时间
```

### 5. detections 检测结果表

用于保存 YOLO 推理结果。

```text
id                  检测结果 ID
image_id            图片 ID
model_id            模型 ID
class_name          检测类别
confidence          置信度
x1                  左上角 x 坐标
y1                  左上角 y 坐标
x2                  右下角 x 坐标
y2                  右下角 y 坐标
result_image_path   检测结果图本地路径
result_image_url    检测结果图访问地址
created_at          检测时间
```

---

## 六、主要功能介绍

### 1. 数据集管理

客户端可以通过接口在服务器上创建数据集，例如：

```text
locomotive_roof_v1
locomotive_roof_test
locomotive_roof_train
```

每个数据集可以包含训练集、验证集、测试集和未分类图片。

---

### 2. 图片上传与管理

客户端可以选择本地图片上传到服务器。服务器会自动完成：

- 保存图片文件；
- 校验图片格式；
- 读取图片宽高；
- 计算 SHA256；
- 生成公网访问 URL；
- 将图片信息写入数据库。

支持图片格式：

```text
jpg
jpeg
png
bmp
webp
```

---

### 3. 模型上传与管理

客户端可以上传训练好的 YOLO 模型文件，格式为：

```text
.pt
```

服务器会把模型保存到：

```text
/data/loco-roof/models
```

同时在数据库中保存模型记录。

系统支持多个模型文件，并且可以设置某个模型为当前启用模型：

```text
active=True
```

检测时如果没有指定模型 ID，服务器会默认使用当前启用模型。

---

### 4. YOLO 检测推理

检测流程如下：

```text
客户端选择图片
        ↓
客户端发送 image_id 到服务器
        ↓
服务器读取图片路径
        ↓
服务器加载当前启用的 .pt 模型
        ↓
YOLOv8 执行目标检测
        ↓
服务器绘制检测框并保存结果图
        ↓
检测结果写入 SQLite
        ↓
返回结果图 URL 和检测框数据给客户端
```

检测结果包含：

```text
类别名称
置信度
检测框坐标
检测结果图 URL
检测时间
```

---

### 5. 前端对比展示

客户端右侧提供原图与检测图对比展示。

```text
左侧：服务器原始图片
右侧：服务器 YOLO 检测结果图
```

这样可以直观看到检测框位置，适合答辩展示和系统演示。

---

### 6. 系统统计功能

客户端可以查看服务器统计信息，包括：

```text
数据集数量
图片数量
人工标注数量
模型数量
检测结果数量
```

---

## 七、服务器端部署说明

以下以 Ubuntu 服务器为例。

### 1. 上传代码到服务器

建议放到：

```bash
/opt/loco-roof/server_cloud
```

### 2. 初始化服务器

进入 `server_cloud` 目录后执行：

```bash
sudo bash scripts/init_server_ubuntu.sh
```

该脚本会完成：

- 更新系统；
- 设置时区；
- 创建普通用户 `app`；
- 安装 Python、Nginx、SQLite 等；
- 创建 2GB swap；
- 创建项目目录；
- 创建数据目录；
- 放行 80、443、SSH 端口。

---

### 3. 安装后端依赖

```bash
cd /opt/loco-roof/server_cloud
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果服务器内存较小，安装 `ultralytics` 可能较慢，建议保持 SSH 连接稳定。

---

### 4. 配置环境变量

```bash
cp .env.example .env
nano .env
```

重点修改：

```env
API_KEY=换成你自己的复杂密钥
PUBLIC_BASE_URL=http://你的公网IP:8000
```

如果使用 Nginx 代理 80 端口，则可以写成：

```env
PUBLIC_BASE_URL=http://你的公网IP
```

注意：`PUBLIC_BASE_URL` 必须带 `http://` 或 `https://`，否则客户端会出现如下错误：

```text
No connection adapters were found
```

---

### 5. 测试启动后端

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

浏览器访问：

```text
http://你的公网IP:8000/docs
```

如果能看到 FastAPI 文档页面，说明后端启动成功。

---

### 6. 使用 systemd 后台运行

```bash
sudo cp deploy/loco-roof.service /etc/systemd/system/loco-roof.service
sudo systemctl daemon-reload
sudo systemctl enable loco-roof
sudo systemctl start loco-roof
sudo systemctl status loco-roof
```

查看后端日志：

```bash
journalctl -u loco-roof -f
```

---

### 7. 配置 Nginx 反向代理

```bash
sudo cp deploy/nginx-loco-roof.conf /etc/nginx/sites-available/loco-roof
sudo ln -s /etc/nginx/sites-available/loco-roof /etc/nginx/sites-enabled/loco-roof
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

配置完成后访问：

```text
http://你的公网IP/docs
```

---

## 八、客户端运行说明

### 1. 安装客户端依赖

Windows：

```bash
cd client_interface
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux / macOS：

```bash
cd client_interface
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 2. 修改客户端配置

打开：

```text
client_interface/client/config.py
```

修改：

```python
SERVER_URL = "http://你的公网IP:8000"
API_KEY = "服务器 .env 中配置的 API_KEY"
```

如果你已经配置了 Nginx，使用 80 端口访问，则写成：

```python
SERVER_URL = "http://你的公网IP"
```

---

### 3. 启动客户端

```bash
python main.py
```

---

### 4. 客户端使用流程

```text
1. 点击“测试连接”
2. 创建数据集
3. 上传测试图片
4. 上传 .pt 模型
5. 激活模型
6. 点击图片列表中的图片
7. 点击“检测当前图片”
8. 查看左侧原图和右侧检测结果图
9. 查看类别、置信度和坐标信息
```

---

## 九、主要接口说明

FastAPI 启动后可以通过 `/docs` 查看完整接口文档。

常用接口如下：

### 1. 健康检查

```http
GET /health
```

用于测试服务器是否在线。

---

### 2. 创建数据集

```http
POST /api/datasets
```

请求体：

```json
{
  "name": "locomotive_roof_v1",
  "description": "机车车顶异物识别数据集"
}
```

---

### 3. 查看数据集列表

```http
GET /api/datasets
```

---

### 4. 上传图片

```http
POST /api/datasets/{dataset_id}/images
```

表单参数：

```text
split = train / val / test / unassigned
file  = 图片文件
```

---

### 5. 查看图片列表

```http
GET /api/datasets/{dataset_id}/images
```

可选参数：

```text
split=test
```

---

### 6. 上传模型

```http
POST /api/models/upload
```

表单参数：

```text
name   = 模型名称
active = true
file   = best.pt
```

---

### 7. 激活模型

```http
POST /api/models/{model_id}/activate
```

---

### 8. 检测图片

```http
POST /api/images/{image_id}/detect
```

可选参数：

```text
conf=0.25
model_id=1
```

返回内容包括：

```text
image_id
result_image_url
detections
```

---

### 9. 查看检测结果

```http
GET /api/images/{image_id}/detections
```

---

### 10. 查看系统统计

```http
GET /api/stats
```

---

## 十、服务器配置建议

你的当前服务器配置如果是：

```text
内存：2GB
硬盘：40GB
公网 IPv4：1 个
带宽：200M
```

建议这样使用：

| 用途 | 是否适合 |
|---|---|
| 保存 5000 张左右图片 | 可以，但要注意硬盘大小 |
| 保存 SQLite 数据库 | 可以 |
| 提供 FastAPI 接口 | 可以 |
| 上传和管理模型 | 可以 |
| 单张图片 YOLO 检测 | 可以尝试，建议用 YOLOv8n / YOLOv8s |
| 大批量并发检测 | 不建议 |
| 训练 YOLO 模型 | 不建议 |

硬盘估算：

| 图片平均大小 | 5000 张占用 |
|---|---|
| 1MB | 约 5GB |
| 2MB | 约 10GB |
| 5MB | 约 25GB |
| 8MB | 约 40GB |

如果图片平均超过 5MB，建议升级到 80GB 或 100GB 硬盘。

---

## 十一、常见问题

### 1. 图片下载失败：No connection adapters were found

原因：服务器返回的图片 URL 没有带 `http://` 或 `https://`。

错误示例：

```text
154.8.177.102:8000/files/dataset_1/test/xxx.jpg
```

正确示例：

```text
http://154.8.177.102:8000/files/dataset_1/test/xxx.jpg
```

解决方法：

```bash
cd /opt/loco-roof/server_cloud
nano .env
```

修改：

```env
PUBLIC_BASE_URL=http://154.8.177.102:8000
```

然后重启：

```bash
sudo systemctl restart loco-roof
```

如果旧数据已经写入数据库，可以重新上传图片，或者修复数据库中的 URL。

---

### 2. 客户端连接不上服务器

检查：

```text
1. SERVER_URL 是否写对
2. 是否带 http://
3. 服务器后端是否启动
4. 云服务器安全组是否放行 8000 或 80 端口
5. Linux 防火墙是否放行端口
```

测试：

```text
http://你的公网IP:8000/docs
```

---

### 3. 检测时报没有可用模型

说明服务器还没有上传 `.pt` 模型，或者模型没有激活。

解决方法：

```text
1. 在客户端上传 .pt 模型
2. 点击“刷新模型列表”
3. 选择模型
4. 点击“激活选中模型”
```

---

### 4. YOLO 检测失败

可能原因：

```text
1. ultralytics 没有安装成功
2. .pt 模型文件损坏
3. 服务器内存不足
4. 图片格式异常
5. 模型类别和任务类型不匹配
```

建议：

```text
优先使用 yolov8n 或 yolov8s 模型
避免在 2GB 内存服务器上运行过大的模型
```

---

### 5. 端口 8000 无法访问

如果直接用 8000 端口，需要确认：

```bash
ufw allow 8000/tcp
```

如果使用 Nginx，则访问：

```text
http://你的公网IP/docs
```

而不是：

```text
http://你的公网IP:8000/docs
```

---

## 十二、项目优化方向

1. **Web 管理后台**  
   后续可以开发 Vue / React 前端，使系统通过浏览器访问，而不是桌面客户端。

2. **批量检测任务队列**  
   当前批量检测是同步执行，后续可以加入 Celery / Redis，实现后台任务队列。

3. **数据集导出功能**  
   可以把数据库中的标注导出为 YOLO 训练格式，方便重新训练模型。

4. **用户权限管理**  
   当前使用 API Key 简单鉴权，后续可以增加登录、用户角色和权限控制。

5. **模型版本管理**  
   可以记录模型训练时间、训练数据集、mAP、Precision、Recall 等指标。

6. **检测结果统计分析**  
   可以统计不同类别异物数量、检测频率、置信度分布等。

7. **视频流检测**  
   后续可以接入 RTSP 摄像头或视频文件，实现实时视频检测。

8. **对象存储扩展**  
   当图片数量变多时，可以使用阿里云 OSS、腾讯云 COS 或 MinIO 保存图片。

9. **数据库升级**  
   数据量增大后，可以从 SQLite 升级到 PostgreSQL 或 MySQL。

10. **GPU 推理服务**  
    如果需要高并发或视频实时检测，可以把 YOLO 推理服务迁移到 GPU 服务器。

---

## 十三、联系方式

如有任何问题或建议，可以通过以下方式联系：

- 邮箱：3449402681@qq.com
- GitHub：hikari551
- 个人博客：[https://hikari551.github.io/](https://hikari551.github.io/)

感谢关注和支持！
