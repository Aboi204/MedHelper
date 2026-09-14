"""
محرك الشرح الطبي الأكاديمي المتعمق (Deep Medical Explainer Engine).
يقوم بدمج محتوى المحاضرة مع بصمة الأستاذ لتوليد شرح أسطوري يتفوق على مجرد القراءة أو التلخيص.
"""

import os
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

from src.pedagogy_extractor import get_gemini_client, load_profile

DEFAULT_ACADEMIC_SYSTEM_PROMPT = """
أنت أستاذ طب وأكاديمي مصري وعربي محنك ورائد (على نمط الأستاذ الدكتور عبد المتعال فودة).
مهمتك: شرح المحاضرة الطبية المرفوعة شرحاً أكاديمياً إكلينيكياً عميقاً ومبسطاً، لا يكتفي بقراءة السلايدات، بل يبني الفهم من الجذور.

قواعد الشرح الإلزامية:
1. الشرح بلغة عربية أكاديمية سلسة وسياقية.
2. الحفاظ الصارم على المصطلحات الطبية بالإنجليزية كما هي دون تعريب مشوه، مع وضع كل مصطلح إنجليزي داخل وسم <bdi> مصطلح </bdi> التزاماً بقواعد اتجاه النصوص (BiDi).
3. التأصيل الفسيولوجي الطبيعي أولاً: لا تبدأ بالمرض أو الدواء، بل ابدأ بـ "العضو أو المستقبل بيعمل إيه طبيعياً في الجسم؟".
4. التفسير بالمبادئ الأولية (First Principles): اشرح "لماذا وكيف؟" (Mechanisms) واجعل الطالب يستنتج الأعراض الجانبية وموانع الاستعمال من صميم الميكانيزم دون حفظ أصم.
5. استباق فخاخ الامتحانات واللبس الشائع (Clinical Pearls & Pitfalls).
6. دعم الشرح بجداول مقارنة واضحة ومخططات تدفق ذهنية (Mermaid Diagrams).
7. ختام الشرح بكبسولة تثبيت سريعة وماتريكس للامتحان.
"""


def explain_lecture(
    lecture_text: str,
    doctor_profile_name: Optional[str] = "dr_abdelmotaal_fouda",
    custom_profile: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.6-flash",
    additional_notes: str = ""
) -> Dict[str, Any]:
    """
    توليد الشرح الأكاديمي للمحاضرة استناداً إلى بصمة الأستاذ المختار.
    """
    if not lecture_text or len(lecture_text.strip()) < 50:
        return {
            "success": False,
            "error": "محتوى المحاضرة قصير جداً أو فارغ.",
        }

    # جلب البروفايل
    profile = custom_profile
    if not profile and doctor_profile_name:
        profile = load_profile(doctor_profile_name)

    # تجهيز البرومبت التوجيهي (System Instruction)
    system_instruction = DEFAULT_ACADEMIC_SYSTEM_PROMPT
    doctor_display_name = "كبار الأساتذة الأكاديميين (أسلوب د. عبد المتعال فودة)"

    if profile:
        doctor_display_name = profile.get("doctor_name", doctor_profile_name)
        blueprint = profile.get("system_prompt_blueprint", "")
        if blueprint:
            system_instruction = f"""
{DEFAULT_ACADEMIC_SYSTEM_PROMPT}

توجيهات إضافية مستخرجة من بصمة أسلوب التدريس المعتمدة للأستاذ ({doctor_display_name}):
----------------------------------------------------------------------
{blueprint}
----------------------------------------------------------------------
التزم التزاماً دقيقاً بهذا المنطق البيداغوجي وتسلسل بناء الفهم أثناء الشرح.
"""

    user_prompt = f"""
المحاضرة الطبية المطلوب شرحها بالتفصيل:
==================================================
{lecture_text}
==================================================

{f"ملاحظات أو تركيز إضافي مطلوب من الطالب: {additional_notes}" if additional_notes else ""}

المطلوب:
اشرح هذه المحاضرة شرحاً وافياً وفق منطق وتكنيك الشرح الأكاديمي المعتمد.
تأكد من:
- التمهيد والتأصيل الفسيولوجي.
- بناء الشرح خطوة بخطوة بالآليات والعلل.
- استنتاج التطبيقات والمحاذير السريرية.
- إدراج مخطط ذهني واحد على الأقل بصيغة ```mermaid``` لتوضيح تسلسل الفكرة.
- إبراز اللآلئ السريرية (Clinical Pearls) وفخاخ الامتحانات.
- إحاطة أي مصطلح إنجليزي أو رقم طبي داخل وسم <bdi>...</bdi>.
"""

    try:
        client = get_gemini_client(api_key)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,  # توازن ممتاز بين الإبداع التعليمي والدقة العلمية الصارمة
        )

        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=config,
        )

        explanation = response.text or ""

        return {
            "success": True,
            "doctor_name": doctor_display_name,
            "explanation": explanation,
            "model_used": model_name,
            "lecture_words": len(lecture_text.split()),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"فشل في توليد الشرح: {str(e)}",
        }
