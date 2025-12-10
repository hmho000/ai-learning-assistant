# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

# ========================================================
# 自动配置逻辑
# ========================================================

# 1. 定义需要特殊处理（收集所有资源/数据）的库
# 这些库通常包含非 Python 文件（如模板、JS、CSS 等），PyInstaller 默认可能漏掉
# 如果以后添加了类似的库，只需确保它在 requirements.txt 中，或者手动添加到这里
COMPLEX_PACKAGES = [
    'docx',             # python-docx (需要模板)
    'gradio',           # Gradio (需要前端资源)
    'streamlit',        # Streamlit
    'pyecharts',        # Pyecharts (需要地图/JS)
    'altair',
    'matplotlib',
    'tkinter',
    'webview',
]

# 2. 动态读取 requirements.txt 获取 hiddenimports
# 这样以后添加纯 Python 依赖时，通常不需要手动修改 spec
def get_requirements():
    reqs = []
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 处理版本号，如 "fastapi>=0.68" -> "fastapi"
                    pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                    if pkg:
                        reqs.append(pkg)
    return reqs

requirements = get_requirements()
print(f"[INFO] Found requirements: {requirements}")

# 3. 准备动态收集的列表
dynamic_datas = []
dynamic_binaries = []
dynamic_hiddenimports = []

# 基础 hiddenimports (有些内置库或间接依赖可能不在 requirements.txt 中)
base_hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'engineio.async_drivers.aiohttp',
    'python_multipart',
    # 显式添加之前版本中存在但被漏掉的模块
    'fastapi.staticfiles',
    'fastapi.templating',
    'fastapi.middleware.cors',
    'starlette',
    'email_validator',
    'charset_normalizer',
    'urllib3',
    'idna',
    'certifi',
    # 补充标准库和别名
    'sqlite3',
    'fitz',
]
dynamic_hiddenimports.extend(base_hiddenimports)

# 自动收集 fastapi 和 uvicorn 的子模块
try:
    dynamic_hiddenimports.extend(collect_submodules('fastapi'))
    dynamic_hiddenimports.extend(collect_submodules('uvicorn'))
except Exception as e:
    print(f"[WARN] Failed to collect submodules: {e}")

# 将 requirements.txt 中的所有包都加入 hiddenimports (防患于未然)
dynamic_hiddenimports.extend(requirements)

# 4. 对复杂包进行 collect_all
for pkg in requirements:
    # 检查是否在复杂包列表中 (模糊匹配，例如 python-docx 对应 docx)
    # 这里做个简单的映射或直接尝试收集
    target_pkg = pkg
    
    # 特殊映射处理
    if pkg == 'python-docx': target_pkg = 'docx'
    if pkg == 'opencv-python': target_pkg = 'cv2'
    if pkg == 'Pillow': target_pkg = 'PIL'
    
    # 如果在复杂列表中，或者我们想激进一点，可以对所有包尝试 collect_all
    # 但为了包大小，我们还是只对白名单里的包做 collect_all
    if target_pkg in COMPLEX_PACKAGES or pkg in COMPLEX_PACKAGES:
        print(f"[INFO] Collecting all resources for: {target_pkg}")
        try:
            tmp_datas, tmp_binaries, tmp_hidden = collect_all(target_pkg)
            dynamic_datas.extend(tmp_datas)
            dynamic_binaries.extend(tmp_binaries)
            dynamic_hiddenimports.extend(tmp_hidden)
        except Exception as e:
            print(f"[WARN] Failed to collect {target_pkg}: {e}")

# 去重
dynamic_datas = list(set(dynamic_datas))
# binaries 不能简单 set，因为是 tuple list，不过 PyInstaller 会处理
dynamic_hiddenimports = list(set(dynamic_hiddenimports))

# ========================================================
# PyInstaller 配置
# ========================================================

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=dynamic_binaries,
    datas=[
        ('backend', 'backend'),  # Include backend package
        ('frontend/dist', 'frontend/dist'), # Include frontend build artifacts
        ('.env.template', '.') # Include env template
    ] + dynamic_datas,
    hiddenimports=dynamic_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='run_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
