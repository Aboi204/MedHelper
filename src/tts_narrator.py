"""
وحدة توليد النطق الصوتي الطبي الأكاديمي باستخدام edge-tts المجانية بنسبة 100%.
توفر أصواتاً عصبية بشرية فائقة النقاء باللغتين العربية والإنجليزية.
"""

import os
import re
import asyncio
from typing import Dict, Any, Optional
import edge_tts

# الأصوات الموصى بها للشرح الطبي
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
    # إزالة أي كتل برمجية أخرى
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # إزالة وسوم bdi و html
    text = re.sub(r"<[^>]+>", "", text)
    # تحويل العناوين # إلى نص عادي
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    # إزالة علامات التنسيق مثل ** و * و __ و `
    text = re.sub(r"[*_`]", "", text)
    # استبدال فواصل الجداول | بفواصل عادية
    text = re.sub(r"\|", " ", text)
    # إزالة الروابط الماركداون [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # تنظيف المسافات والأسطر الفارغة الزائدة
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def _generate_audio_async(text: str, output_path: str, voice_id: str, rate: str = "+0%") -> None:
    """
    دالة غير متزامنة لتوليد ملف الصوت وحفظه.
    """
    communicate = edge_tts.Communicate(text, voice_id, rate=rate)
    await communicate.save(output_path)


def generate_audio(
    text: str,
    output_filename: str = "lecture_explanation.mp3",
    voice_key: str = "ar-EG-Shakir",
    output_dir: str = "audio_outputs",
    rate: str = "+0%"
) -> Dict[str, Any]:
    """
    الدالة الرئيسية لتوليد الصوت من النص الطبي.
    """
    cleaned_text = clean_markdown_for_speech(text)
    if not cleaned_text:
        return {"success": False, "error": "النص فارغ بعد التنظيف."}

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    voice_info = RECOMMENDED_VOICES.get(voice_key, RECOMMENDED_VOICES["ar-EG-Shakir"])
    voice_id = voice_info["id"]

    try:
        # تشغيل الدالة غير المتزامنة داخل الحلقة المناسبة
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # إذا كان هناك loop نشط بالفعل (مثل سياق Streamlit/Jupyter)
            import nest_asyncio
            nest_asyncio.apply()
            loop.run_until_complete(_generate_audio_async(cleaned_text, output_path, voice_id, rate))
        else:
            loop.run_until_complete(_generate_audio_async(cleaned_text, output_path, voice_id, rate))

        return {
            "success": True,
            "file_path": output_path,
            "voice_used": voice_info["name"],
            "character_count": len(cleaned_text),
        }
    except Exception as e:
        # محاولة أخيرة بـ asyncio.run
        try:
            asyncio.run(_generate_audio_async(cleaned_text, output_path, voice_id, rate))
            return {
                "success": True,
                "file_path": output_path,
                "voice_used": voice_info["name"],
                "character_count": len(cleaned_text),
            }
        except Exception as err2:
            return {"success": False, "error": f"فشل في توليد الصوت: {str(err2)}"}
