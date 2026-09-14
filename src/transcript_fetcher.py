"""
وحدة سحب ومعالجة تفريغ المحاضرات من يوتيوب والملفات النصية.
أداة مجانية 100% ومفتوحة المصدر.
"""

import re
from typing import Optional, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi


def extract_youtube_video_id(url_or_id: str) -> Optional[str]:
    """
    استخراج معرف فيديو يوتيوب (Video ID) من أي صيغة رابط.
    """
    url_or_id = url_or_id.strip()
    # لو كان المعرف مدخل مباشرة (11 حرف)
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id

    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:shorts\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def fetch_youtube_transcript(url_or_id: str, languages=("ar", "en")) -> Dict[str, Any]:
    """
    سحب التفريغ النصي لمقطع يوتيوب بدقة مع دعم اللغتين العربية والإنجليزية.
    """
    video_id = extract_youtube_video_id(url_or_id)
    if not video_id:
        return {
            "success": False,
            "error": "تعذر استخراج معرف الفيديو من الرابط المدخل. يرجى التأكد من صحة الرابط.",
            "video_id": None,
            "transcript_text": "",
        }

    try:
        # جلب قائمة اللغات المتوفرة
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # محاولة العثور على التفريغ باللغة المفضلة
        transcript = None
        try:
            transcript = transcript_list.find_transcript(list(languages))
        except Exception:
            # لو لم نجد تفريغ يدوي باللغات المطلوبة، نحاول جلب التفريغ التلقائي
            try:
                transcript = transcript_list.find_generated_transcript(list(languages))
            except Exception:
                # إذا تعذر، نجلب أول تفريغ متوفر أياً كانت لغته
                for t in transcript_list:
                    transcript = t
                    break

        if not transcript:
            return {
                "success": False,
                "error": "لم يتم العثور على أي تفريغ نصي (Subtitles/Captions) لهذا الفيديو.",
                "video_id": video_id,
                "transcript_text": "",
            }

        fetched_data = transcript.fetch()
        full_text = " ".join([entry["text"] for entry in fetched_data])
        # تنظيف الفراغات المتكررة
        cleaned_text = re.sub(r"\s+", " ", full_text).strip()

        return {
            "success": True,
            "video_id": video_id,
            "language": transcript.language,
            "is_generated": transcript.is_generated,
            "transcript_text": cleaned_text,
            "total_words": len(cleaned_text.split()),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"حدث خطأ أثناء سحب التفريغ: {str(e)}",
            "video_id": video_id,
            "transcript_text": "",
        }
