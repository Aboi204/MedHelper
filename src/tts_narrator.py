"""
وحدة توليد النطق الصوتي الطبي الأكاديمي السريع عبر edge-tts.
تستخدم عملية منفصلة (Subprocess) لعزل الصوت تماماً عن حلقة Streamlit ومنع أي تعليق أو بطء.
"""

import os
import re
import tempfile
import subprocess
from typing import Dict, Any

RECOMMENDED_VOICES = {
    "ar-EG-Shakir": {
        "id": "ar-EG-ShakirNeural",
        "name": "شاكر (مصري طبيعي - وقور وأكاديمي)",
        "lang": "ar",
    },
    "ar-EG-Salma": {
        "id": "ar-EG-SalmaNeural",
        "name": "سلمى (مصرية طبيعية - واضحة ومخارج ممتازة)",
        "lang": "ar",
    },
    "ar-SA-Hamed": {
        "id": "ar-SA-HamedNeural",
        "name": "حامد (عربي فصيح - نبرة إلقاء)",
        "lang": "ar",
    },
    "en-US-Andrew": {
        "id": "en-US-AndrewNeural",
        "name": "Andrew (أمريكي أكاديمي - دقيق)",
        "lang": "en",
    },
}


def clean_markdown_for_speech(text: str) -> str:
    """
    تنظيف نصوص الماركداون من الرموز البرمجية والمخططات والجداول حتى يقرأ الصوت نصاً طبيعياً سلساً.
    """
    # إزالة كتل كود mermaid والمخططات
    text = re.sub(r"```mermaid.*?```", "", text, flags=re.DOTALL)
    # إزالة أي كتل كود أخرى
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # إزالة وسوم bdi و html
    text = re.sub(r"<[^>]+>", "", text)
    # تحويل العناوين # إلى نص عادي
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    # إزالة علامات التنسيق مثل ** و * و __ و `
    text = re.sub(r"[*_`]", "", text)
    # إزالة فواصل الجداول
    text = re.sub(r"\|", " ", text)
    # إزالة روابط الماركداون
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # تنظيف الفراغات المتكررة
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_audio(
    text: str,
    output_filename: str = "lecture_explanation.mp3",
    voice_key: str = "ar-EG-Shakir",
    output_dir: str = "audio_outputs",
    rate: str = "+15%"
) -> Dict[str, Any]:
    """
    توليد الصوت عبر عملية معزولة وسريعة دون أي تعليق في الواجهة.
    """
    cleaned_text = clean_markdown_for_speech(text)
    if not cleaned_text:
        return {"success": False, "error": "النص فارغ بعد التنظيف."}

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    voice_info = RECOMMENDED_VOICES.get(voice_key, RECOMMENDED_VOICES["ar-EG-Shakir"])
    voice_id = voice_info["id"]

    try:
        # حفظ النص في ملف مؤقت مشفر بـ UTF-8 لتجنب مشاكل الرموز في الأوامر
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as temp_file:
            temp_file.write(cleaned_text)
            temp_file_path = temp_file.name

        cmd = [
            "edge-tts",
            "--file", temp_file_path,
            "--voice", voice_id,
            "--rate", rate,
            "--write-media", output_path
        ]

        # تشغيل الأمر في عملية معزولة مع مهلة أقصاها 90 ثانية
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)

        # حذف الملف المؤقت
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

        if proc.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return {
                "success": True,
                "file_path": output_path,
                "voice_used": voice_info["name"],
                "character_count": len(cleaned_text),
                "words": len(cleaned_text.split()),
            }
        else:
            return {
                "success": False,
                "error": f"فشل توليد الصوت: {proc.stderr or 'لم يتم إنشاء ملف الصوت بنجاح'}",
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "استغرق توليد الصوت وقتاً أطول من المتوقع (Timeout). يُفضل توليد الصوت للكبسولة الصوتية السريعة.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"خطأ أثناء توليد الصوت: {str(e)}",
        }
