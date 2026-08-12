"""
文件转换模块
将上传的文件统一转换为 PDF 格式
- PDF: 直接使用
- 图片: 通过 Pillow 转 PDF
- Office: 通过 LibreOffice Headless 转 PDF
"""
import shutil
import subprocess
from pathlib import Path
from PIL import Image

SUPPORTED_PDF = {".pdf"}
SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
SUPPORTED_OFFICE = {
    ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".odt", ".ods", ".odp",
}


def convert_to_pdf(input_path: Path, output_dir: Path, job_id: str) -> Path:
    """
    将输入文件转换为 PDF

    Returns: PDF 文件路径
    Raises: ValueError 如果格式不支持或转换失败
    """
    ext = input_path.suffix.lower()
    output_path = output_dir / f"{job_id}.pdf"

    if ext in SUPPORTED_PDF:
        shutil.copy2(input_path, output_path)
        return output_path

    if ext in SUPPORTED_IMAGES:
        return _image_to_pdf(input_path, output_path)

    if ext in SUPPORTED_OFFICE:
        return _office_to_pdf(input_path, output_path)

    raise ValueError(
        f"不支持的文件格式: {ext}。"
        f"支持: PDF, 图片(PNG/JPG/GIF/BMP/TIFF/WEBP), "
        f"Office(DOC/DOCX/PPT/PPTX/XLS/XLSX)"
    )


def _image_to_pdf(input_path: Path, output_path: Path) -> Path:
    """图片转 PDF"""
    img = Image.open(input_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(output_path, "PDF", resolution=150.0)
    return output_path


def _office_to_pdf(input_path: Path, output_path: Path) -> Path:
    """Office 文档转 PDF（需要 LibreOffice）"""
    try:
        subprocess.run(
            [
                "libreoffice", "--headless", "--convert-to", "pdf",
                "--outdir", str(output_path.parent),
                str(input_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
    except FileNotFoundError:
        raise ValueError(
            "LibreOffice 未安装，无法转换 Office 文档。"
            "请安装: apt install libreoffice，或直接上传 PDF/图片。"
        )
    except subprocess.TimeoutExpired:
        raise ValueError("LibreOffice 转换超时")

    # LibreOffice 输出文件名为 原文件名.pdf
    expected = output_path.parent / f"{input_path.stem}.pdf"
    if expected.exists():
        if expected != output_path:
            expected.rename(output_path)
        return output_path

    raise ValueError("LibreOffice 转换失败，文件未生成")
