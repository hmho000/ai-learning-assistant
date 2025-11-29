"""
启动 FastAPI 后端（通过 uvicorn），并自动用默认浏览器打开前端页面。
这个脚本将作为 PyInstaller 打包的入口。
"""

import threading
import time
import webbrowser
import sys
import os

try:
    import uvicorn
except ImportError:
    print("[ERROR] 未找到 uvicorn 模块，请先安装：py -m pip install uvicorn")
    input("按 Enter 键退出...")
    sys.exit(1)


def open_browser_delayed():
    """延迟打开浏览器，等待服务启动"""
    time.sleep(2)
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception as e:
        print(f"[WARN] 无法自动打开浏览器: {e}")
        print("请手动访问: http://127.0.0.1:8000")


def load_env():
    """Load environment variables from .env file"""
    env_path = ".env"
    if os.path.exists(env_path):
        print(f"[INFO] Loading environment variables from {env_path}")
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
                except ValueError:
                    pass

def main() -> None:
    """启动 uvicorn 服务并在浏览器中打开首页。"""
    # Load .env first
    load_env()
    
    # 处理打包后的路径：如果是 PyInstaller 打包的 exe，使用 exe 所在目录
    if getattr(sys, "frozen", False):
        # 打包后的 exe 模式
        root = os.path.dirname(sys.executable)
    else:
        # 普通 Python 运行模式
        root = os.path.dirname(os.path.abspath(__file__))
    
    # 确保工作目录正确（影响 backend 模块的导入）
    os.chdir(root)
    
    print("=" * 50)
    print("AI 学习助手 - 启动服务")
    print("=" * 50)
    print(f"工作目录: {root}")
    print("正在启动后端服务...")
    print("服务地址: http://127.0.0.1:8000")
    print("=" * 50)
    print()
    
    # 在后台线程中延迟打开浏览器
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    try:
        # 直接运行 uvicorn（而不是通过 subprocess）
        # 这样在打包后的 exe 中也能正常工作
        uvicorn.run(
            "backend.app:app",
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n[INFO] 收到退出信号，正在关闭服务...")
    except Exception as e:
        print(f"\n[ERROR] 启动服务失败: {e}")
        print("\n可能的原因：")
        print("1. 端口 8000 已被占用")
        print("2. backend 模块未正确打包到 exe 中")
        print("3. 前端静态文件未正确复制到 dist/frontend/dist")
        input("\n按 Enter 键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()