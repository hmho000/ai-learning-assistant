"""
ocr_demo.py
-----------

独立 OCR 识别脚本：
- 支持命令行输入图片路径
- 使用 pytesseract 识别文字
- 输出识别结果到控制台或文件
"""

import argparse
import sys
from pathlib import Path

try:
    from rapidocr_onnxruntime import RapidOCR
    from PIL import Image
except ImportError:
    RapidOCR = None
    Image = None


def ocr_image(path: Path) -> str:
    """
    使用 RapidOCR 对图片进行 OCR 识别。
    无需安装 Tesseract 软件。
    """
    if not RapidOCR or not Image:
        raise ImportError("请先安装依赖：pip install rapidocr_onnxruntime Pillow")
    
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}")

    try:
        # 初始化 OCR 引擎
        # det_use_cuda, cls_use_cuda, rec_use_cuda 默认为 False，使用 CPU 推理，兼容性最好
        engine = RapidOCR()
        
        # 识别
        # result 是一个 list，每个元素是 [points, text, score]
        result, _ = engine(str(path))
        
        if not result:
            return ""
            
        # 拼接所有文本
        texts = [line[1] for line in result]
        return "\n".join(texts)
        
    except Exception as e:
        raise RuntimeError(f"OCR 识别失败：{e}") from e


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR 文字识别工具")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="图片文件路径",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出文本文件路径（可选，默认打印到控制台）",
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    try:
        text = ocr_image(input_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"成功识别 {len(text)} 个字符。")
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"结果已保存到：{output_path}")
    else:
        print("---------------- 识别内容 ----------------")
        print(text)
        print("-----------------------------------------")


if __name__ == "__main__":
    main()
