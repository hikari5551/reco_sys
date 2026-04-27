import sys
import os
# 打印当前的路径和关键信息
print("=== 系统路径 ===")
print(sys.path)
print("\n=== 项目根目录 ===")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(BASE_DIR)
print("\n=== 关键文件是否存在 ===")
print(f"utils文件夹: {os.path.exists(os.path.join(BASE_DIR, 'utils'))}")
print(f"utils/__init__.py: {os.path.exists(os.path.join(BASE_DIR, 'utils', '__init__.py'))}")
print(f"utils/GlobalLog.py: {os.path.exists(os.path.join(BASE_DIR, 'utils', 'GlobalLog.py'))}")

# 强制把项目根目录加入sys.path（即使你之前加了，这里再强制加一次）
sys.path.insert(0, BASE_DIR)

print("\n=== 开始测试导入 ===")
try:
    from utils.GlobalLog import LoggerCat
    print("✅ 直接导入utils.GlobalLog成功")
except Exception as e:
    print(f"❌ 直接导入失败: {e}")

try:
    from utils import LoggerCat
    print("✅ 通过utils包导入LoggerCat成功")
except Exception as e:
    print(f"❌ 通过utils包导入失败: {e}")
