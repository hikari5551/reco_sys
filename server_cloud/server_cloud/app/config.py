import os
from pathlib import Path

# =========================================================
# 后端配置文件
# =========================================================
# 服务器端负责保存数据集、测试集、模型文件，并执行 YOLO 推理。
# 客户端只调用接口，不再保存模型，也不再运行 yolo.py。
# =========================================================

APP_NAME = os.getenv("APP_NAME", "Locomotive Roof Foreign Object Detection API")

# API_KEY 用于公网接口鉴权，正式部署时必须改成复杂字符串。
API_KEY = os.getenv("API_KEY", "change-this-long-random-key")

# 数据根目录，建议放在 /data 下，便于后续扩容和备份。
DATA_ROOT = Path(os.getenv("DATA_ROOT", "/data/loco-roof")).resolve()

# SQLite 数据库路径。5000 张图片级别的元数据管理用 SQLite 足够。
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_ROOT / 'db' / 'app.db'}")

# 对外访问地址。部署后改成 http://公网IP 或 https://域名。
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# 文件目录规划。
UPLOAD_DIR = DATA_ROOT / "uploads"      # 数据集和测试集图片
MODEL_DIR = DATA_ROOT / "models"        # .pt 模型
RESULT_DIR = DATA_ROOT / "results"      # 检测结果图
DB_DIR = DATA_ROOT / "db"               # SQLite 数据库
LOG_DIR = DATA_ROOT / "logs"            # 日志

# 启动时自动创建目录，避免目录不存在导致报错。
for path in [UPLOAD_DIR, MODEL_DIR, RESULT_DIR, DB_DIR, LOG_DIR]:
    path.mkdir(parents=True, exist_ok=True)
