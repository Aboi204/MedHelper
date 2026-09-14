"""
وحدة التحليل البيداغوجي وتوليد بصمة الشرح الطبي.
تستخدم Google Gemini API (المجاني 100%) لتحليل تفريغ المحاضرات وحفظ البروفايل.
"""

import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.pedagogy_prompt import PEDAGOGY_EXTRACTION_SYSTEM_PROMPT, build_extraction_prompt

load_dotenv()


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """
    إنشاء عميل Google GenAI باستخدام المفتاح المخزن أو الممرر.
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "لم يتم العثور على مفتاح Google Gemini API. "
            "يرجى ضبط GEMINI_API_KEY في ملف .env أو إدخاله مباشرة."
        )
    return genai.Client(api_key=key)


def analyze_pedagogy(
    transcript_text: str,
    doctor_name: str,
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.6-flash"
) -> Dict[str, Any]:
    """
    تحليل تفريغ المحاضرة واستخراج الركائز الـ 11 وبصمة الشرح التنفيذية.
    """
    if not transcript_text or len(transcript_text.strip()) < 100:
        return {
            "success": False,
            "error": "نص تفريغ المحاضرة قصير جداً أو غير صالح للتحليل.",
        }

    try:
        client = get_gemini_client(api_key)
        user_prompt = build_extraction_prompt(transcript_text, doctor_name)

        config = types.GenerateContentConfig(
            system_instruction=PEDAGOGY_EXTRACTION_SYSTEM_PROMPT,
            temperature=0.3,  # درجة حرارة منخفضة لضمان دقة التحليل الأكاديمي والالتزام الصارم بالركائز
        )

        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=config,
        )

        analysis_result = response.text or ""

        # استخراج البرومبت التنفيذي من الناتج
        system_prompt_blueprint = ""
        blueprint_match = re.search(
            r"###\s*\[?System Prompt Blueprint[^\]]*\]?:?\s*(.*)",
            analysis_result,
            re.DOTALL | re.IGNORECASE
        )
        if blueprint_match:
            system_prompt_blueprint = blueprint_match.group(1).strip()
        else:
            # إذا لم يتم العثور على العنوان بشكل صريح، نأخذ الثلث الأخير كقالب تنفيذي
            system_prompt_blueprint = analysis_result

        profile_data = {
            "doctor_name": doctor_name,
            "model_used": model_name,
            "total_words_analyzed": len(transcript_text.split()),
            "full_analysis": analysis_result,
            "system_prompt_blueprint": system_prompt_blueprint,
        }

        # حفظ البروفايل محلياً في مجلد profiles
        save_profile(doctor_name, profile_data)

        return {
            "success": True,
            "doctor_name": doctor_name,
            "profile": profile_data,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"حدث خطأ أثناء تحليل الأسلوب بالذكاء الاصطناعي: {str(e)}",
        }


def save_profile(doctor_name: str, profile_data: Dict[str, Any], profiles_dir: str = "profiles") -> str:
    """
    حفظ بروفايل الأستاذ في ملف JSON منظم داخل مجلد profiles.
    """
    os.makedirs(profiles_dir, exist_ok=True)
    # تنظيف اسم الملف
    safe_name = re.sub(r"[^\w\-]", "_", doctor_name.strip()).lower()
    file_path = os.path.join(profiles_dir, f"{safe_name}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)

    return file_path


def load_profile(doctor_name_or_file: str, profiles_dir: str = "profiles") -> Optional[Dict[str, Any]]:
    """
    تحميل بروفايل أستاذ تم تحليله مسبقاً.
    """
    safe_name = re.sub(r"[^\w\-]", "_", doctor_name_or_file.strip()).lower()
    potential_paths = [
        doctor_name_or_file,
        os.path.join(profiles_dir, f"{safe_name}.json"),
        os.path.join(profiles_dir, f"{doctor_name_or_file}.json"),
    ]

    for p in potential_paths:
        if os.path.exists(p) and os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return None
