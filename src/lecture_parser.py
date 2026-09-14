"""
وحدة قراءة وتفكيك ملفات المحاضرات الطبية (PDF, PPTX, TXT).
تستخرج النصوص والعناوين والجداول بكفاءة مجاناً 100%.
"""

import os
from typing import Dict, Any, List
import pymupdf
from pptx import Presentation


def parse_pdf_lecture(file_path: str) -> Dict[str, Any]:
    """
    قراءة ملف PDF واستخراج محتوى السلايدات أو الصفحات.
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"الملف غير موجود: {file_path}"}

    try:
        doc = pymupdf.open(file_path)
        slides_text: List[str] = []
        full_content: List[str] = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if text:
                slides_text.append(f"--- [صفحة / سلايد {page_num + 1}] ---\n{text}")
                full_content.append(text)

        combined_text = "\n\n".join(slides_text)
        return {
            "success": True,
            "total_pages": len(doc),
            "content": combined_text,
            "raw_text": "\n".join(full_content),
            "word_count": len(combined_text.split()),
        }
    except Exception as e:
        return {"success": False, "error": f"فشل في قراءة ملف الـ PDF: {str(e)}"}


def parse_pptx_lecture(file_path: str) -> Dict[str, Any]:
    """
    قراءة ملف PowerPoint (.pptx) واستخراج محتوى السلايدات.
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"الملف غير موجود: {file_path}"}

    try:
        prs = Presentation(file_path)
        slides_text: List[str] = []
        full_content: List[str] = []

        for idx, slide in enumerate(prs.slides, start=1):
            slide_parts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        txt = paragraph.text.strip()
                        if txt:
                            slide_parts.append(txt)
            if slide_parts:
                slide_content = "\n".join(slide_parts)
                slides_text.append(f"--- [سلايد {idx}] ---\n{slide_content}")
                full_content.append(slide_content)

        combined_text = "\n\n".join(slides_text)
        return {
            "success": True,
            "total_pages": len(prs.slides),
            "content": combined_text,
            "raw_text": "\n".join(full_content),
            "word_count": len(combined_text.split()),
        }
    except Exception as e:
        return {"success": False, "error": f"فشل في قراءة ملف الـ PowerPoint: {str(e)}"}


def parse_lecture_file(file_path: str) -> Dict[str, Any]:
    """
    المعالج العام لملفات المحاضرات بمختلف أنواعها.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return parse_pdf_lecture(file_path)
    elif ext in [".pptx", ".ppt"]:
        return parse_pptx_lecture(file_path)
    elif ext in [".txt", ".md"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            return {
                "success": True,
                "total_pages": 1,
                "content": text,
                "raw_text": text,
                "word_count": len(text.split()),
            }
        except Exception as e:
            return {"success": False, "error": f"فشل في قراءة الملف النصي: {str(e)}"}
    else:
        return {
            "success": False,
            "error": f"صيغة الملف ({ext}) غير مدعومة حالياً. الصيغ المدعومة: PDF, PPTX, TXT.",
        }
