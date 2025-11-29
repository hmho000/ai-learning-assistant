# AI Learning Assistant

基于课程资料自动生成学习练习题的智能学习助手。

## 📌 项目简介

AI Learning Assistant 是一个面向大学生设计的智能学习辅助项目。
你只需上传课程 **PDF 教材**，系统即可自动解析章节，并利用 DeepSeek AI 自动生成：

- ✔ **选择题** (支持自定义数量)
- ✔ **填空题** (支持自定义数量)
- ⬜ 简答题（规划中）
- ⬜ 难度分级练习（规划中）
- ⬜ 复习计划（基于艾宾浩斯记忆曲线）（规划中）

本项目旨在帮助大学生更高效地复习课程，提升知识掌握度，同时降低教师制作题目的工作量。

---

## 🎯 核心功能清单

### 📖 1. 课程资料解析
- ✔ **PDF 解析**：基于 PyMuPDF 精准提取文本
- ✔ **目录识别**：自动识别 PDF 目录（TOC）并按章节拆分内容
- ✔ **智能降噪**：自动消除页码、竖排装饰文字、断行合并
- ⬜ 支持 PPT 文档（规划中）
- ⬜ 支持 Word 文档（规划中）

### 📝 2. 自动生成题库
系统基于 DeepSeek API 生成：
- ✔ **单选题**（multiple_choice）
- ✔ **填空题**（fill_in_blank）
- ✔ **自定义数量**：**[NEW]** 支持自定义每章生成的选择题和填空题数量
- ✔ **智能过滤**：自动剔除依赖算法编号/例题编号的题目
- ✔ **多知识点覆盖**：确保题目覆盖章节多个核心概念
- ⬜ 多选题（规划中）
- ⬜ 判断题（规划中）
- ⬜ 简答题（规划中）
- ⬜ 代码题（规划中）
- ⬜ 按难度分类（规划中）

### 🎨 3. 前端展示与交互
- ✔ **React + Vite + TailwindCSS** 现代化界面
- ✔ **看题模式**：**[NEW]** 优化的阅读界面，支持查看选项、答案和详细解析
- ✔ **答题模式**：沉浸式答题环境，实时反馈，自动评分
- ✔ **本地存储**：答题结果自动保存
- ⬜ 错题本（规划中）
- ⬜ 学习报告（规划中）

### 🚀 4. 批量处理与自动化
- ✔ 一键启动前后端服务 (`run_app.py`)
- ✔ 自动同步生成结果到前端
- ✔ 支持后台异步任务处理

### 📅 5. 个性化复习计划（规划中）
- ⬜ 结合艾宾浩斯曲线自动安排复习日程
- ⬜ 记录每次答题结果
- ⬜ 动态调节复习节奏

---

## 🧠 项目技术架构

### 🔧 后端 (Backend)
- **FastAPI**: 高性能 Web 框架
- **SQLModel (SQLite)**: 数据库 ORM
- **PyMuPDF**: PDF 处理
- **DeepSeek API**: 大模型服务

### 🎨 前端 (Frontend)
- **React 18**: UI 库
- **Vite**: 构建工具
- **TailwindCSS**: 样式引擎
- **Lucide React**: 图标库

### 📁 项目结构

```plaintext
ai-learning-assistant/
│
├── run_app.py              # [入口] 启动脚本 (启动 FastAPI + 托管前端 + 打开浏览器)
├── ai_learning.db          # SQLite 数据库文件
├── .env                    # 环境变量配置 (API Key)
│
├── backend/                # 后端源码
│   ├── app.py              # FastAPI 应用入口 & API 路由
│   ├── models.py           # SQLModel 数据库模型 (Course, Chapter, Quiz, Question)
│   ├── services.py         # 核心业务逻辑 (PDF解析, AI出题)
│   └── database.py         # 数据库连接配置
│
├── frontend/               # 前端源码
│   ├── dist/               # [构建产物] React 打包后的静态文件
│   ├── src/
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx       # 首页/上传页
│   │   │   ├── CourseConfigPage.jsx # [NEW] 生成配置页
│   │   │   └── QuestionsPage.jsx    # 答题/看题页
│   │   ├── components/
│   │   │   ├── quiz/                # 答题组件 (QuizReviewView, QuizExamView)
│   │   │   └── GenerationProgress.jsx # 生成进度条
│   │   └── api.ts                   # 前端 API 封装
│   └── package.json
│
└── data/                   # [自动生成] 存放上传的 PDF 文件
```

---

## 🚀 快速开始

### 1. 环境准备
- Python 3.10+
- Node.js 16+ (仅开发需要，运行无需)
- DeepSeek API Key

### 2. 安装依赖

**后端依赖**:
```bash
pip install fastapi uvicorn sqlmodel pymupdf requests python-multipart
```

**前端依赖** (仅需修改前端代码时):
```bash
cd frontend
npm install
```

### 3. 配置 API Key
在项目根目录创建 `.env` 文件：
```ini
DEEPSEEK_API_KEY=your_api_key_here
```

### 4. 启动应用

**方式一：直接运行 (推荐)**
```bash
python run_app.py
```
此命令会：
1. 启动 FastAPI 后端 (http://127.0.0.1:8000)
2. 自动打开默认浏览器

**方式二：开发模式**
- 后端: `uvicorn backend.app:app --reload`
- 前端: `cd frontend && npm run dev`

---

## 🔄 更新日志

### v1.2.0 - 2025-11-30
- **✨ 新增功能**
  - **题目数量配置**：在生成前可自定义每章的选择题和填空题数量。
  - **UI 优化**：重构了选择题显示组件，修复了选项不显示的问题，界面更加美观。
- **🔧 架构升级**
  - 全面转向 FastAPI + SQLite 架构，废弃了旧版的纯脚本模式。
  - 完善了 `run_app.py` 启动流程。

### v1.1.0 - 2025-11-29
- 支持 PDF 拖拽上传。
- 新增课程管理与删除功能。

### v1.0.0 - 2025-11-28
- 初始化版本，支持基础的 PDF 解析与 AI 出题。

---

## 📄 许可证
[LICENSE](LICENSE)
