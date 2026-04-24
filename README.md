├── config/              # 配置文件目录
├── models/              # 模型文件目录（存放 .pt 文件）
├── test_images/         # 测试图片目录
├── utils/               # 工具模块（日志、报警、全局变量等）
├── yoloshow/            # 界面模块
│   ├── Windows.py       # 主窗口与对比模式窗口
│   └── ChangeWindow.py  # 窗口切换逻辑
├── yolov8l-best.pt      # 训练好的YOLO模型
├── yolo.py              # 模型推理核心模块
├── main.py              # 程序入口
└── requirements.txt     # 依赖清单
