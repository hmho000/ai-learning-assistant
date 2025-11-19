# AI Learning Assistant  
基于课程资料自动生成学习练习题的智能学习助手

## 📌 项目简介
AI Learning Assistant 是一个面向大学生设计的智能学习辅助项目。  
你只需上传课程 **PPT / PDF / 教材电子书**，系统即可自动生成：

- ✔ 选择题  
- ✔ 填空题  
- ✔ 简答题  
- ✔ 难度分级练习  
- ✔ 复习计划（基于艾宾浩斯记忆曲线）  

本项目旨在帮助大学生更高效地复习课程，提升知识掌握度，同时降低教师制作题目的工作量。

---

## 🎯 核心功能

### 📖 1. 课程资料解析
- 支持 PDF、PPT、Word 文档
- 自动抽取章节结构、知识点、重点内容
- 自动消除噪声（如页眉、页脚、水印）

### 📝 2. 自动生成题库
系统基于大语言模型（ChatGPT API / Qwen / Gemini）生成：
- 多选题、单选题
- 填空题
- 判断题
- 简答题
- 代码题（如数据结构、程序设计课程）

并支持按难度分类：
- ⭐ 基础入门  
- ⭐⭐ 中级理解  
- ⭐⭐⭐ 提升挑战  

### 📅 3. 个性化复习计划
结合艾宾浩斯曲线自动安排复习日程：
- 第 1 天：首次学习  
- 第 2 天：复习  
- 第 4 天：第二次复习  
- 第 7 天：第三次复习  
- 第 15 天：巩固复习  

并记录每次答题结果，动态调节复习节奏。

### 📊 4. 错题本 & 学习报告
系统自动记录：
- 错题  
- 易错知识点  
- 掌握度趋势图  
并生成每周学习报告与改进建议。

---

## 🧠 项目技术架构

### 🔧 后端
- **Python 3.10+**
- **Flask / FastAPI**
- 文档解析库：PyMuPDF、python-pptx、pdfplumber
- 向量数据库（可选）：Milvus / FAISS
- AI API：ChatGPT / Qwen / Gemini / 本地 Llama

### 🎨 前端（可选）
- React + Vite  
- TailwindCSS  
- Ant Design  

### 🗄 数据库
- SQLite（开发测试）
- MySQL / PostgreSQL（生产）

### ☁ 部署
- Gitee Pages（前端）
- 云服务器 / Render / Railway（后端）

---

## 📂 项目结构（建议）

```plaintext
ai-learning-assistant/
│
├── backend/
│   ├── app.py
│   ├── api/
│   ├── services/
│   ├── utils/
│   └── models/
│
├── frontend/
│   ├── src/
│   ├── pages/
│   ├── components/
│   └── assets/
│
├── data/
│   ├── uploads/
│   └── samples/
│
├── docs/
│   └── 项目立项书.docx
│
└── README.md
