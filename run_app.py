"""
启动 AI Learning Assistant 全栈应用。
架构：FastAPI (Backend) + SQLite (Database) + React (Frontend)
功能：启动后端 API 服务，托管前端静态资源，并自动打开浏览器。
此脚本也是 PyInstaller 打包的入口文件。
"""

import threading
import time
import webbrowser
import sys
import os
import subprocess
import shutil

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
    """从 .env 文件加载环境变量"""
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

def check_and_build_frontend(root_dir: str):
    """
    检查前端构建是否存在，如果不存在则尝试自动构建。
    """
    frontend_dir = os.path.join(root_dir, "frontend")
    dist_dir = os.path.join(frontend_dir, "dist")
    
    if os.path.exists(dist_dir) and os.path.isdir(dist_dir):
        # print("[INFO] 前端构建目录已存在，跳过构建。")
        return

    print(f"[WARN] 未找到前端构建目录: {dist_dir}")
    print("[INFO] 尝试自动构建前端...")
    
    # 检查 npm 是否可用
    if shutil.which("npm") is None:
        print("[ERROR] 未找到 npm 命令，无法自动构建前端。")
        print("请手动安装 Node.js 和 npm，并在 frontend/ 目录下运行 `npm run build`。")
        return

    try:
        # 1. npm install
        print("[INFO] 正在运行 npm install...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, shell=True)
        
        # 2. npm run build
        print("[INFO] 正在运行 npm run build...")
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, shell=True)
        
        print("[INFO] 前端构建成功！")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 前端构建失败: {e}")
        print("[INFO] 尝试执行清理并重新安装依赖...")
        
        # 尝试清理 node_modules 和 package-lock.json
        node_modules_path = os.path.join(frontend_dir, "node_modules")
        package_lock_path = os.path.join(frontend_dir, "package-lock.json")
        
        try:
            if os.path.exists(node_modules_path):
                print(f"[INFO] 删除 {node_modules_path} ...")
                # Windows 下有时候会因为权限问题删除失败，尝试使用 shell 命令
                if os.name == 'nt':
                    subprocess.run(["rmdir", "/s", "/q", "node_modules"], cwd=frontend_dir, shell=True)
                else:
                    shutil.rmtree(node_modules_path)
            
            if os.path.exists(package_lock_path):
                print(f"[INFO] 删除 {package_lock_path} ...")
                try:
                    os.remove(package_lock_path)
                except OSError:
                     pass # 如果删除锁定文件失败则忽略
                
            print("[INFO] 重新运行 npm install...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, shell=True)
            
            print("[INFO] 重新运行 npm run build...")
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, shell=True)
            
            print("[INFO] 前端重新构建成功！")
            
        except Exception as retry_e:
            print(f"[ERROR] 重新构建仍然失败: {retry_e}")
            print("请尝试手动进入 frontend 目录执行清理和构建操作。")
    except Exception as e:
        print(f"[ERROR] 构建过程中发生意外错误: {e}")

def main() -> None:
    """启动 uvicorn 服务并在浏览器中打开首页。"""
    # 首先加载 .env
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
    
    # 检查并自动构建前端
    check_and_build_frontend(root)
    
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