# AI Learning Assistant  
基于课程资料自动生成学习练习题的智能学习助手

## 📌 项目简介
AI Learning Assistant 是一个面向大学生设计的智能学习辅助项目。  
你只需上传课程 **PPT / PDF / 教材电子书**，系统即可自动生成：

- ✔ 选择题  
- ✔ 填空题  
- ⬜ 简答题（规划中）
- ⬜ 难度分级练习（规划中）
- ⬜ 复习计划（基于艾宾浩斯记忆曲线）（规划中）

本项目旨在帮助大学生更高效地复习课程，提升知识掌握度，同时降低教师制作题目的工作量。

---

## 🎯 核心功能清单

### 📖 1. 课程资料解析
- ✔ 支持 PDF 文档解析（使用 PyMuPDF）
- ✔ 基于 PDF 目录（TOC）精准定位章节，失效时自动回退到正则扫描
- ✔ 自动消除噪声（页码、竖排装饰文字、断行合并）
- ⬜ 支持 PPT 文档（规划中）
- ⬜ 支持 Word 文档（规划中）

### 📝 2. 自动生成题库
系统基于 DeepSeek API 生成：
- ✔ 单选题（multiple_choice）
- ✔ 填空题（fill_in_blank）
- ✔ 自动生成章节元数据（meta）：章节标题、题库标题、描述
- ✔ 题目质量过滤：自动剔除依赖算法编号/例题编号的题目
- ✔ 最低题量兜底：自动补充题目确保每种题型至少 5 道
- ✔ 多知识点覆盖：确保题目覆盖章节多个核心概念
- ⬜ 多选题（规划中）
- ⬜ 判断题（规划中）
- ⬜ 简答题（规划中）
- ⬜ 代码题（规划中）
- ⬜ 按难度分类（规划中）

### 🚀 3. 批量处理与自动化
- ✔ 一键批量处理多章节（`scripts/run_all.py`）
- ✔ 自动同步 Markdown 到前端目录
- ✔ 自动更新 manifest.json（章节清单）
- ✔ 支持跳过已存在文件（`--skip-existing`）
- ✔ 支持显示答案模式（`--show-answer`）

### 🎨 4. 前端展示
- ✔ React + Vite + TypeScript 前端界面
- ✔ Markdown 题库渲染（使用 react-markdown）
- ✔ 章节下拉选择器
- ✔ 动态加载章节题库
- ✔ TailwindCSS 美化样式
- ✔ **答题交互功能**（已实现）
  - ✔ 阅读模式：查看 Markdown 格式的题库
  - ✔ 答题模式：交互式答题，支持一次性提交所有答案
  - ✔ 自动评分：提交后自动计算得分和正确率
  - ✔ 答题结果展示：显示错题列表、正确答案和解析
  - ✔ 本地存储：答题结果自动保存到 localStorage
- ✔ 练习模式：每道题独立作答，实时反馈（已实现）
- ⬜ 错题本（规划中）
- ⬜ 学习报告（规划中）

### 📅 5. 个性化复习计划（规划中）
- ⬜ 结合艾宾浩斯曲线自动安排复习日程
- ⬜ 记录每次答题结果
- ⬜ 动态调节复习节奏

### 📊 6. 错题本 & 学习报告（规划中）
- ⬜ 自动记录错题
- ⬜ 易错知识点统计
- ⬜ 掌握度趋势图
- ⬜ 每周学习报告与改进建议

---

## 🧠 项目技术架构

### 🔧 后端
- **Python 3.10+**
- **PyMuPDF (fitz)**：PDF 解析
- **requests**：HTTP 请求
- **DeepSeek API**：AI 出题
- **argparse**：命令行参数解析
- **pathlib**：路径处理

### 🎨 前端
- **React 18.3+**
- **Vite 5.4+**
- **TypeScript**：类型安全
- **react-markdown**：Markdown 渲染
- **react-router-dom**：路由管理
- **TailwindCSS 3.4+**：样式框架

### 📁 项目结构

```plaintext
ai-learning-assistant/
│
├── backend/              # 后端代码（规划中）
│
├── frontend/             # 前端代码
│   ├── src/
│   │   ├── components/   # React 组件
│   │   │   ├── quiz/     # 答题相关组件
│   │   │   │   ├── QuizView.tsx              # 练习模式组件
│   │   │   │   ├── QuizExamView.tsx          # 答题模式组件
│   │   │   │   ├── MultipleChoiceQuestion.tsx      # 练习模式选择题
│   │   │   │   ├── MultipleChoiceQuestionExam.tsx  # 答题模式选择题
│   │   │   │   ├── FillInBlankQuestion.tsx         # 练习模式填空题
│   │   │   │   ├── FillInBlankQuestionExam.tsx     # 答题模式填空题
│   │   │   │   ├── QuizSummary.tsx           # 练习模式总结
│   │   │   │   └── QuizExamSummary.tsx       # 答题模式总结
│   │   │   └── QuestionViewer.jsx            # Markdown 阅读器
│   │   ├── pages/        # 页面组件
│   │   │   └── QuestionsPage.jsx             # 题库页面（支持阅读/答题模式切换）
│   │   ├── types/        # TypeScript 类型定义
│   │   │   └── quiz.ts   # 题库相关类型
│   │   ├── utils/        # 工具函数
│   │   │   ├── quizUtils.ts      # 题库工具函数
│   │   │   └── quizStorage.ts    # 本地存储管理
│   │   └── App.jsx       # 主应用
│   ├── public/
│   │   └── questions/    # 题库文件
│   │       ├── manifest.json           # 章节清单
│   │       ├── ch*_questions.md        # Markdown 格式题库
│   │       └── ch*_questions.json      # JSON 格式题库（答题模式使用）
│   └── package.json
│
├── experiments/          # 实验脚本
│   ├── parse_pdf_demo.py        # PDF 解析脚本
│   ├── generate_questions_demo.py # AI 出题脚本
│   └── render_questions_demo.py  # Markdown 渲染脚本
│
├── scripts/              # 工具脚本
│   └── run_all.py        # 一键批量处理脚本
│
├── data/                 # 数据目录
│   └── *.pdf            # 教材 PDF 文件
│
├── docs/                 # 文档目录
│
└── README.md
```

---

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+（用于前端）
- DeepSeek API Key

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-learning-assistant
```

2. **安装 Python 依赖**
```bash
pip install pymupdf requests
```

3. **配置 API Key**
```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your_api_key_here"

# Linux/Mac
export DEEPSEEK_API_KEY="your_api_key_here"
```

4. **安装前端依赖**
```bash
cd frontend
npm install
```

### 使用示例

#### 1. 生成单章节题库
```powershell
# 生成第1章题库
python .\scripts\run_all.py `
  --chapters "1" `
  --chapter-titles "绪论"
```

#### 2. 批量生成多章节
```powershell
# 生成第1-3章题库
python .\scripts\run_all.py `
  --pdf ".\data\数据结构（C语言版）（第3版）双色版 (李冬梅,严蔚敏,吴伟民) (Z-Library).pdf" `
  --output-dir ".\experiments\output" `
  --chapters "1,2,3" `
  --chapter-titles "绪论,线性表,栈和队列" `
  --show-answer
```

#### 3. 启动前端查看题库
```powershell
cd frontend
npm run dev
```

然后在浏览器访问 `http://localhost:5173` 查看生成的题库。

**前端功能说明**：
- **阅读模式**：点击"阅读题库"按钮，以 Markdown 格式查看题库内容
- **答题模式**：点击"开始答题"按钮，进入交互式答题界面
  - 填写所有题目后，点击"提交答案"一次性提交
  - 系统自动计算得分并显示答题结果
  - 答题结果会保存到浏览器本地存储

**注意**：答题模式需要 JSON 格式的题库文件。如果只有 Markdown 文件，需要确保对应的 JSON 文件（`ch{id}_questions.json`）已复制到 `frontend/public/questions/` 目录。

---

## 📝 脚本说明

### `experiments/parse_pdf_demo.py`
从 PDF 中提取指定章节的文本内容，优先根据目录（TOC）定位章节，必要时回退到正则扫描。

**用法：**
```bash
python experiments/parse_pdf_demo.py \
  --chapter "第2章" \
  --output experiments/output/ch2_clean.txt \
  --pdf data/教材.pdf
```

日志会打印所用模式（TOC / 兜底）、匹配到的章节标题以及页码范围，便于核对提取结果。

### `experiments/generate_questions_demo.py`
调用 DeepSeek API 生成题库 JSON。

**用法：**
```bash
python experiments/generate_questions_demo.py \
  --input experiments/output/ch2_clean.txt \
  --output experiments/output/ch2_questions.json \
  --chapter-id 2 \
  --chapter-title "第2章 线性表"
```

**特性：**
- 自动生成章节元数据（meta）
- 题目质量过滤（剔除编号依赖题）
- 最低题量兜底（自动补充题目）

### `experiments/render_questions_demo.py`
将题库 JSON 渲染为 Markdown 并更新 manifest.json。

**用法：**
```bash
python experiments/render_questions_demo.py \
  --input experiments/output/ch2_questions.json \
  --output frontend/public/questions/ch2_questions.md \
  --show-answer
```

### `scripts/run_all.py`
一键批量处理多章节的完整流程。

**用法：**
```bash
python scripts/run_all.py \
  --chapters "1,2,3" \
  --chapter-titles "绪论,线性表,栈和队列" \
  --show-answer \
  --skip-existing
```

**参数说明：**
- `--pdf`：PDF 文件路径（默认：`data/数据结构...pdf`）
- `--output-dir`：输出目录（默认：`experiments/output`）
- `--chapters`：章节列表，逗号分隔（例如：`"1,2,3"`）
- `--chapter-titles`：章节标题列表，与章节一一对应
- `--show-answer`：生成时显示答案与解析
- `--skip-existing`：跳过已存在的文件

---

## 🔒 安全说明

**注意：** 脚本中包含默认的 API Key（用于快速测试）。在生产环境中，建议：
- 通过环境变量 `DEEPSEEK_API_KEY` 设置
- 或使用 `--api-key` 参数覆盖
- 不要将包含真实 API Key 的代码提交到公开仓库

---

## 📄 许可证

详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

如有问题或建议，请通过 Issue 反馈。
