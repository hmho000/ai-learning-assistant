@echo off
chcp 65001 >nul
setlocal ENABLEDELAYEDEXPANSION

echo ============================================
echo AI 学习助手 - Windows 一键打包脚本
echo ============================================
echo 当前步骤会依次执行：
echo   1. 安装 Python 后端依赖
echo   2. 构建前端 (npm install + npm run build)
echo   3. 使用 PyInstaller 打包為 run_app.exe
echo   4. 拷贝前端 dist 静态资源到 exe 同级目录
echo.

REM 确保从脚本所在目录执行（防止从其它路径双击导致相对路径错乱）
cd /d "%~dp0"

REM === 0. 环境检查：Python / pip / npm 是否可用 ===
where py >nul 2>nul
IF ERRORLEVEL 1 (
  echo [ERROR] 未找到 ^"py^" 命令，请先安装 Python（并勾选 ^"Add python.exe to PATH^"）。
  echo 可从官网下载安装: https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

where npm >nul 2>nul
IF ERRORLEVEL 1 (
  echo [ERROR] 未找到 ^"npm^" 命令，请先安装 Node.js（官网安装包会自动配置 npm）。
  echo 可从官网下载: https://nodejs.org/en/download
  pause
  exit /b 1
)

REM === 1. 安装后端依赖（使用 Windows 推荐的 py -m pip） ===
echo [1/4] 安装后端 Python 依赖：requirements.txt
call py -m pip install -r requirements.txt
IF ERRORLEVEL 1 (
  echo [ERROR] pip install 失败，请检查 Python / 网络环境后重试。
  pause
  exit /b 1
)

REM === 2. 构建前端 ===
echo.
echo [2/4] 构建前端（npm install ^& npm run build）
cd frontend
REM 如果用的是 yarn 或 pnpm，可以自行替换下面两行为 yarn / pnpm
call npm install
IF ERRORLEVEL 1 (
  echo [ERROR] npm install 失败，请确认 Node.js/npm 安装是否正常。
  pause
  exit /b 1
)

call npm run build
IF ERRORLEVEL 1 (
  echo [ERROR] npm run build 失败，请先确保前端工程能正常单独运行（npm run dev）。
  pause
  exit /b 1
)
cd ..

REM === 3. 用 PyInstaller 打包 run_app.py 为单文件可执行程序 ===
echo.
echo [3/4] 使用 PyInstaller 打包为单文件 exe

REM 检查并删除旧的 exe 文件（如果存在且被占用，会提示用户）
if exist dist\run_app.exe (
  echo 检测到旧的 run_app.exe，正在尝试删除...
  del /F /Q dist\run_app.exe 2>nul
  if exist dist\run_app.exe (
    echo [WARN] 无法删除旧的 run_app.exe，可能正在运行或被其他程序占用。
    echo 请先关闭所有正在运行的 run_app.exe 进程，然后重新运行此脚本。
    pause
    exit /b 1
  )
  echo 已删除旧的 exe 文件。
)

call py -m pip show pyinstaller >nul 2>nul
IF ERRORLEVEL 1 (
  echo 未检测到 PyInstaller，正在自动安装...
  call py -m pip install pyinstaller
  IF ERRORLEVEL 1 (
    echo [ERROR] 安装 PyInstaller 失败，请手动执行：py -m pip install pyinstaller
    pause
    exit /b 1
  )
)

REM 使用 run_app.spec 文件打包（包含必要的隐藏导入配置）
call py -m PyInstaller run_app.spec
IF ERRORLEVEL 1 (
  echo [ERROR] PyInstaller 打包失败
  echo.
  echo 可能的原因：
  echo 1. 旧的 run_app.exe 正在运行，请先关闭它
  echo 2. 文件被其他程序占用（如杀毒软件、文件管理器）
  echo 3. 权限不足，请以管理员身份运行此脚本
  pause
  exit /b 1
)

REM === 4. 将前端构建产物复制到 exe 同级目录的 frontend/dist（供打包程序访问静态资源） ===
echo.
echo [4/4] 拷贝前端静态资源到 dist\frontend\dist
if not exist dist\frontend mkdir dist\frontend
xcopy /E /I /Y "frontend\dist" "dist\frontend\dist"

echo.
echo ============================================
echo 打包完成！可执行文件路径：
echo   dist\run_app.exe
echo 双击该 exe 即可启动后端并自动打开浏览器。
echo ============================================
echo.
echo [完成] 打包流程结束。
pause
endlocal