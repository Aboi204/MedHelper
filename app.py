"""
واجهة تطبيق MedHelper التفاعلية المبنية بـ Streamlit.
منصة الشرح الطبي الأكاديمي الذكي بأسلوب كبار الأساتذة.
مجانية 100% وبدون أي تكلفة.
"""

import os
import glob
import json
import streamlit as st
from dotenv import load_dotenv

from src.transcript_fetcher import fetch_youtube_transcript
from src.pedagogy_extractor import analyze_pedagogy, load_profile
from src.lecture_parser import parse_lecture_file
from src.explainer_engine import explain_lecture
from src.tts_narrator import generate_audio, RECOMMENDED_VOICES

load_dotenv()

# إعدادات صفحة Streamlit
st.set_page_config(
    page_title="MedHelper | نظام الشرح الطبي الأكاديمي",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص CSS للغة العربية واتجاه النصوص
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    /* ضبط اتجاه العناصر والمدخلات */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        direction: rtl;
        text-align: right;
    }
    
    /* بطاقات مميزة للعناوين */
    .med-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .pearl-box {
        background-color: #fff3cd;
        border-right: 5px solid #ffc107;
        padding: 15px;
        border-radius: 8px;
        color: #856404;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)


# الشريط الجانبي: ضبط الإعدادات ومفتاح API
with st.sidebar:
    st.image("https://img.icons8.com/color/96/stethoscope.png", width=70)
    st.title("🩺 إعدادات MedHelper")
    st.caption("نظام الشرح الطبي الأكاديمي المتقدم")
    
    saved_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "مفتاح Google Gemini API المجاني:",
        value=saved_key,
        type="password",
        help="يمكنك الحصول عليه مجاناً 100% في دقيقة من Google AI Studio"
    )
    
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.success("✅ مفتاح الذكاء الاصطناعي متصل وجاهز!")
    else:
        st.warning("⚠️ يرجى إدخال مفتاح Gemini API للبدء.")
        st.markdown("[👉 اضغط هنا لاستخراج مفتاحك المجاني في دقيقة](https://aistudio.google.com/)")

    st.divider()
    st.markdown("### 🎙️ إعدادات الصوت الطبي")
    voice_options = list(RECOMMENDED_VOICES.keys())
    voice_labels = [RECOMMENDED_VOICES[k]["name"] for k in voice_options]
    selected_voice_label = st.selectbox("صوت القارئ الأكاديمي:", voice_labels, index=0)
    selected_voice_key = voice_options[voice_labels.index(selected_voice_label)]

    st.divider()
    st.info("💡 **قاعدة التكلفة الصفرية:** كل الأدوات والنماذج والمكتبات المستخدمة هنا مجانية ومفتوحة المصدر بالكامل بنسبة 100%.")


# رأس الصفحة الرئيسي
st.markdown("""
<div class="med-card">
    <h1 style="margin:0; font-size: 2.2rem; color: #ffffff;">🩺 منصة MedHelper للشرح الطبي الأكاديمي</h1>
    <p style="margin: 8px 0 0 0; font-size: 1.1rem; color: #e0e8f5;">
        تدريب نماذج الذكاء الاصطناعي على منطق وتكنيك كبار الأساتذة (نموذج د. عبد المتعال فودة) لتقديم شرح حقيقي عميق ومبسط للمحاضرات
    </p>
</div>
""", unsafe_allow_html=True)

# التبويبات الرئيسية
tab_explain, tab_lab = st.tabs([
    "📚 شرح المحاضرات الطبية (Lecture Explainer)",
    "🔬 مختبر استخراج بصمة الأستاذ (Style Blueprint Lab)"
])


# ==============================================================================
# التبويب الأول: شرح المحاضرات الطبية
# ==============================================================================
with tab_explain:
    st.subheader("📖 ارفع محاضرتك واحصل على الشرح الأكاديمي الأسطوري")
    st.write("يقوم النظام بقراءة ملف المحاضرة، وتفكيك آلياتها الفسيولوجية والإكلينيكية، وتوليد شرح متوسع بأسلوب الدكتور المختار.")

    col1, col2 = st.columns([1, 1])

    with col1:
        # البحث عن البروفايلات المحفوظة
        profile_files = glob.glob("profiles/*.json")
        profile_names = []
        profile_map = {}

        for pf in profile_files:
            try:
                with open(pf, "r", encoding="utf-8") as f:
                    pdata = json.load(f)
                    dname = pdata.get("doctor_name", os.path.basename(pf))
                    profile_names.append(dname)
                    profile_map[dname] = pf
            except Exception:
                pass

        if not profile_names:
            profile_names = ["د. عبد المتعال فودة (افتراضي)"]
            selected_profile_name = profile_names[0]
            selected_profile_path = "profiles/dr_abdelmotaal_fouda.json"
        else:
            selected_profile_name = st.selectbox("اختر أسلوب وتكنيك الدكتور:", profile_names, index=0)
            selected_profile_path = profile_map.get(selected_profile_name, "profiles/dr_abdelmotaal_fouda.json")

    with col2:
        additional_notes = st.text_input(
            "ملاحظات أو تركيز خاص تريده في الشرح (اختياري):",
            placeholder="مثال: ركز على أسئلة الامتحانات، أو ركز على ميكانيزم الـ Beta-blockers"
        )

    # رفع ملف المحاضرة أو إدخال النص
    upload_type = st.radio("طريقة إدخال المحاضرة:", ["رفع ملف (PDF / PowerPoint / TXT)", "كتابة أو لصق نص المحاضرة مباشرة"], horizontal=True)

    lecture_text_to_explain = ""

    if upload_type == "رفع ملف (PDF / PowerPoint / TXT)":
        uploaded_file = st.file_uploader("اختر ملف المحاضرة:", type=["pdf", "pptx", "ppt", "txt", "md"])
        if uploaded_file:
            # حفظ مؤقت للملف
            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            parse_res = parse_lecture_file(temp_path)
            if parse_res["success"]:
                lecture_text_to_explain = parse_res["content"]
                st.success(f"✅ تم تحميل المحاضرة بنجاح! ({parse_res.get('total_pages', 1)} صفحات/سلايدات - {parse_res.get('word_count', 0)} كلمة)")
                with st.expander("👁️ عرض النص المستخرج من المحاضرة"):
                    st.text_area("النص المستخرج:", lecture_text_to_explain[:2500] + ("..." if len(lecture_text_to_explain) > 2500 else ""), height=200)
            else:
                st.error(parse_res["error"])
    else:
        lecture_text_to_explain = st.text_area(
            "الصق نص المحاضرة أو السلايدات هنا:",
            height=250,
            placeholder="مثال:\nAutonomic Nervous System: Sympathetic vs Parasympathetic receptors and clinical applications..."
        )

    st.write("")
    explain_btn = st.button("🚀 توليد الشرح الأكاديمي المتعمق", type="primary", use_container_width=True)

    if explain_btn:
        if not os.getenv("GEMINI_API_KEY"):
            st.error("❌ يرجى إدخال مفتاح Google Gemini API في القائمة الجانبية أولاً.")
        elif not lecture_text_to_explain or len(lecture_text_to_explain.strip()) < 30:
            st.warning("⚠️ يرجى رفع ملف المحاضرة أو لصق نص المحاضرة قبل بدء الشرح.")
        else:
            with st.spinner(f"جاري صياغة الشرح الأكاديمي الأسطوري بأسلوب {selected_profile_name}... يرجى الانتظار ثوانٍ معدودة"):
                res = explain_lecture(
                    lecture_text=lecture_text_to_explain,
                    doctor_profile_name=selected_profile_path,
                    additional_notes=additional_notes
                )

                if res["success"]:
                    st.session_state["last_explanation"] = res["explanation"]
                    st.session_state["doctor_name"] = res["doctor_name"]
                    st.success("🎉 تم توليد الشرح الأكاديمي بنجاح!")
                else:
                    st.error(res["error"])

    # عرض الشرح والأزرار التفاعلية
    if "last_explanation" in st.session_state:
        st.divider()
        st.markdown(f"### 📋 الشرح الأكاديمي الكامل — بأسلوب: <bdi>{st.session_state.get('doctor_name', '')}</bdi>", unsafe_allow_html=True)
        
        # عرض نص الشرح بالماركداون
        st.markdown(st.session_state["last_explanation"], unsafe_allow_html=True)

        st.divider()
        c_audio, c_download = st.columns([1, 1])

        with c_audio:
            if st.button("🎙️ الاستماع للشرح الصوتي (Edge-TTS AI Voice)", use_container_width=True):
                with st.spinner("جاري تحويل الشرح الطبي إلى صوت أكاديمي نقي..."):
                    audio_res = generate_audio(
                        text=st.session_state["last_explanation"],
                        output_filename="latest_lecture.mp3",
                        voice_key=selected_voice_key
                    )
                    if audio_res["success"]:
                        st.audio(audio_res["file_path"], format="audio/mp3")
                        st.success(f"✅ تم توليد الصوت بنجاح بصوت {audio_res['voice_used']}!")
                    else:
                        st.error(audio_res["error"])

        with c_download:
            st.download_button(
                label="📥 تحميل الشرح كملف نصي (Markdown)",
                data=st.session_state["last_explanation"],
                file_name="medical_lecture_explanation.md",
                mime="text/markdown",
                use_container_width=True
            )


# ==============================================================================
# التبويب الثاني: مختبر استخراج بصمة الأستاذ
# ==============================================================================
with tab_lab:
    st.subheader("🔬 مختبر استخراج وتفكيك منطق الشرح الأكاديمي")
    st.write("أدخل رابط يوتيوب أو تفريغ نصي لمحاضرة دكتور مميز، ليقوم الذكاء الاصطناعي بتحليل **منطق وهندسة الشرح** (الركائز الـ 11) وتوليد برومبت تنفيذي تلقائي.")

    col_d1, col_d2 = st.columns([1, 1])
    with col_d1:
        doctor_input_name = st.text_input("اسم الدكتور أو الأستاذ:", value="د. عبد المتعال فودة")
    with col_d2:
        model_choice = st.selectbox("نموذج التحليل:", ["gemini-3.6-flash", "gemini-flash-latest"], index=0)

    input_source = st.radio("مصدر تفريغ المحاضرة:", ["رابط مقطع يوتيوب", "لصق تفريغ نصي جاهز (Transcript)"], horizontal=True)

    transcript_to_analyze = ""

    if input_source == "رابط مقطع يوتيوب":
        yt_url = st.text_input("أدخل رابط يوتيوب للمحاضرة:", placeholder="https://www.youtube.com/watch?v=...")
        if yt_url:
            with st.spinner("جاري سحب تفريغ المحاضرة من يوتيوب..."):
                t_res = fetch_youtube_transcript(yt_url)
                if t_res["success"]:
                    transcript_to_analyze = t_res["transcript_text"]
                    st.success(f"✅ تم سحب التفريغ بنجاح! ({t_res['total_words']} كلمة - اللغة: {t_res['language']})")
                    with st.expander("عرض التفريغ المسحوب"):
                        st.text_area("نص التفريغ:", transcript_to_analyze[:2000] + "...", height=150)
                else:
                    st.error(t_res["error"])
    else:
        transcript_to_analyze = st.text_area(
            "الصق تفريغ المحاضرة هنا:",
            height=250,
            placeholder="الصق هنا النص المنطوق للدكتور في المحاضرة بدقة..."
        )

    st.write("")
    analyze_btn = st.button("⚡ تحليل منطق الشرح واستخراج البصمة الأكاديمية (11 ركيزة)", type="primary", use_container_width=True)

    if analyze_btn:
        if not os.getenv("GEMINI_API_KEY"):
            st.error("❌ يرجى إدخال مفتاح Google Gemini API في القائمة الجانبية أولاً.")
        elif not transcript_to_analyze or len(transcript_to_analyze.strip()) < 100:
            st.warning("⚠️ نص تفريغ المحاضرة قصير جداً أو غير موجود. يرجى توفير تفريغ مناسب للتحليل.")
        else:
            with st.spinner(f"جاري تفكيك منطق تدريس {doctor_input_name} وفق الركائز الـ 11 وتوليد البرومبت التنفيذي..."):
                analysis_res = analyze_pedagogy(
                    transcript_text=transcript_to_analyze,
                    doctor_name=doctor_input_name,
                    model_name=model_choice
                )

                if analysis_res["success"]:
                    st.success(f"🎉 تم استخراج بصمة أسلوب {doctor_input_name} وحفظها في مجلد profiles بنجاح!")
                    
                    st.markdown("### 📊 التحليل البيداغوجي الكامل (الركائز الـ 11):")
                    st.markdown(analysis_res["profile"]["full_analysis"])
                    
                    st.divider()
                    st.markdown("### 🧩 البرومبت التنفيذي المولد (System Prompt Blueprint):")
                    st.code(analysis_res["profile"]["system_prompt_blueprint"], language="markdown")
                else:
                    st.error(analysis_res["error"])
