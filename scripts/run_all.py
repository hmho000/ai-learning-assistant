"""
run_all.py
----------

一键调度 PDF 解析、AI 出题、Markdown 渲染与 manifest 更新的脚本。

功能：
- 自动从 PDF 提取章节文本
- 调用 AI 生成题库 JSON（包含 meta 元数据）
- 渲染 Markdown 并更新 manifest.json
- 自动同步 Markdown 到 frontend/public/questions/ 目录

PowerShell 示例：

```powershell
# 一键生成第1章题库并同步到前端
python .\scripts\run_all.py `
  --chapters "1" `
  --chapter-titles "绪论"

# 批量生成多章节
python .\scripts\run_all.py `
  --pdf ".\data\数据结构（C语言版）（第3版）双色版 (李冬梅,严蔚敏,吴伟民) (Z-Library).pdf" `
  --output-dir ".\experiments\output" `
  --chapters "1,2,3" `
  --chapter-titles "绪论,线性表,栈和队列"

# 生成后启动前端开发服务器
cd frontend
npm run dev
```

注意：脚本会自动将生成的 Markdown 文件复制到 frontend/public/questions/ 目录，
无需手动复制。manifest.json 中的 file 字段会自动使用正确的文件名。

整本书处理示例：
```powershell
# 处理整本书所有章节（假设共10章）
python .\scripts\run_all.py `
  --chapters "1,2,3,4,5,6,7,8,9,10" `
  --chapter-titles "绪论,线性表,栈和队列,串,数组和广义表,树和二叉树,图,查找,排序,文件" `
  --skip-existing
```
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF_NAME = "数据结构（C语言版）（第3版）双色版 (李冬梅,严蔚敏,吴伟民) (Z-Library).pdf"
DEFAULT_PDF_PATH = Path("data") / DEFAULT_PDF_NAME
PARSE_SCRIPT = REPO_ROOT / "experiments" / "parse_pdf_demo.py"
GENERATE_SCRIPT = REPO_ROOT / "experiments" / "generate_questions_demo.py"
RENDER_SCRIPT = REPO_ROOT / "experiments" / "render_questions_demo.py"
FRONTEND_QUESTIONS_DIR = REPO_ROOT / "frontend" / "public" / "questions"


def parse_chapters_arg(raw: Optional[str]) -> List[int]:
    if not raw:
        return [1]
    chapters: List[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            chapters.append(int(item))
        except ValueError as exc:
            raise ValueError(f"无法解析章节编号：{item}") from exc
    if not chapters:
        raise ValueError("章节列表为空，请检查 --chapters 参数。")
    return chapters


def parse_titles_arg(raw: Optional[str], expected: int) -> Optional[List[str]]:
    if raw is None:
        return None
    titles = [title.strip() for title in raw.split(",")]
    if len(titles) != expected:
        raise ValueError(
            f"--chapter-titles 数量 ({len(titles)}) 与章节数量 ({expected}) 不一致。"
        )
    return titles


def run_subprocess(command: List[str], cwd: Optional[Path] = None) -> None:
    print(f"[命令] {' '.join(command)}")
    subprocess.run(command, check=True, cwd=str(cwd) if cwd else None)


def chapter_title_label(chapter_id: int, override: Optional[str]) -> str:
    if override:
        return override
    return f"第{chapter_id}章"


def process_chapter(
    chapter_id: int,
    chapter_title: str,
    pdf_path: Path,
    output_dir: Path,
    show_answer: bool,
    skip_existing: bool,
) -> Tuple[Path, Path, Path]:
    chapter_label = f"第 {chapter_id} 章 {chapter_title}".strip()
    clean_txt = output_dir / f"ch{chapter_id}_clean.txt"
    questions_json = output_dir / f"ch{chapter_id}_questions.json"
    markdown_file = output_dir / f"ch{chapter_id}_questions.md"

    print("=" * 80)
    print(f"正在处理：{chapter_label}")
    print("=" * 80)

    # Step 1: 解析 PDF -> Clean TXT
    if skip_existing and clean_txt.exists():
        print(f"[跳过] 已存在清洗文本：{clean_txt}")
    else:
        run_subprocess(
            [
                sys.executable,
                str(PARSE_SCRIPT),
                "--chapter",
                chapter_title,
                "--output",
                str(clean_txt),
                "--pdf",
                str(pdf_path),
            ]
        )

    # Step 2: 生成题目 JSON
    if skip_existing and questions_json.exists():
        print(f"[跳过] 已存在题库 JSON：{questions_json}")
    else:
        run_subprocess(
            [
                sys.executable,
                str(GENERATE_SCRIPT),
                "--input",
                str(clean_txt),
                "--output",
                str(questions_json),
                "--chapter-id",
                str(chapter_id),
                "--chapter-title",
                chapter_title,
            ]
        )

    # Step 3: 渲染 Markdown & 更新 manifest
    if skip_existing and markdown_file.exists():
        print(f"[跳过] 已存在 Markdown：{markdown_file}")
    else:
        cmd = [
            sys.executable,
            str(RENDER_SCRIPT),
            "--input",
            str(questions_json),
            "--output",
            str(markdown_file),
        ]
        if show_answer:
            cmd.append("--show-answer")
        run_subprocess(cmd)

    # Step 4: 同步 Markdown 到前端 public/questions 目录
    try:
        FRONTEND_QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
        target_md = FRONTEND_QUESTIONS_DIR / markdown_file.name
        shutil.copy2(markdown_file, target_md)
        print(f"[同步] 已复制 Markdown 到前端目录：{target_md}")
    except Exception as exc:
        print(f"[警告] 同步 Markdown 到前端目录失败（不影响主流程）：{exc}")

    print(f"[完成] 第 {chapter_id} 章：")
    print(f"  Clean TXT : {clean_txt}")
    print(f"  Questions : {questions_json}")
    print(f"  Markdown  : {markdown_file}")
    return clean_txt, questions_json, markdown_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="批量运行 PDF 解析 -> 出题 -> Markdown 渲染的总调度脚本"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=str(DEFAULT_PDF_PATH),
        help="教材 PDF 路径（默认 data/ 数据结构...pdf）",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(REPO_ROOT / "experiments" / "output"),
        help="输出根目录，默认 ./experiments/output",
    )
    parser.add_argument(
        "--chapters",
        type=str,
        default=None,
        help='需要处理的章节列表，逗号分隔，例如 "1,2,3"',
    )
    parser.add_argument(
        "--chapter-titles",
        type=str,
        default=None,
        help='章节标题列表，与 --chapters 一一对应，例如 "绪论,线性表,栈和队列"',
    )
    parser.add_argument(
        "--show-answer",
        action="store_true",
        help="生成 Markdown 时同时输出答案与解析",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="如果输出文件已存在，则跳过该步骤",
    )

    args = parser.parse_args()

    try:
        chapters = parse_chapters_arg(args.chapters)
        titles = parse_titles_arg(args.chapter_titles, len(chapters)) if args.chapter_titles else None
    except ValueError as exc:
        parser.error(str(exc))

    pdf_path = Path(args.pdf).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"PDF 路径：{pdf_path}")
    print(f"输出目录：{output_dir}")
    print(f"章节列表：{chapters}")
    if titles:
        print(f"章节标题：{titles}")
    else:
        print("章节标题：未提供，将使用“第X章”格式。")

    for idx, chapter_id in enumerate(chapters):
        title_override = titles[idx] if titles else None
        chapter_title = chapter_title_label(chapter_id, title_override)
        try:
            process_chapter(
                chapter_id=chapter_id,
                chapter_title=chapter_title,
                pdf_path=pdf_path,
                output_dir=output_dir,
                show_answer=args.show_answer,
                skip_existing=args.skip_existing,
            )
        except subprocess.CalledProcessError as exc:
            print(f"[错误] 第 {chapter_id} 章处理失败：{exc}", file=sys.stderr)
            sys.exit(exc.returncode or 1)

    print("所有章节处理完成。")


if __name__ == "__main__":
    main()

