#!/usr/bin/env bash
set -e

# 1. 安装后端依赖
pip install -r requirements.txt

# 2. 构建前端
cd frontend
# 如果用的是 yarn 或 pnpm，可以自行替换为 yarn / pnpm
npm install
npm run build
cd ..

# 3. 用 PyInstaller 打包 run_app.py 为单文件可执行程序
python -m PyInstaller -F run_app.py

# 4. 将前端构建产物复制到 exe 同级目录的 frontend/dist（供打包程序访问静态资源）
mkdir -p dist/frontend
cp -r frontend/dist dist/frontend/dist

echo "打包完成，可执行文件在 dist/run_app 或 dist/run_app.exe 中。"


