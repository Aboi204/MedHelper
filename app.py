"""
واجهة تطبيق MedHelper التفاعلية المبنية بـ Streamlit.
منصة الشرح الطبي الأكاديمي الذكي بأسلوب كبار الأساتذة (نموذج د. عبد المتعال فودة).
مجانية 100% وبدون أي تكلفة مالية.
"""

import os
import streamlit as st
from dotenv import load_dotenv

from src.lecture_parser import parse_lecture_file
from src.explainer_engine import explain_lecture
from src.tts_narrator import generate_audio, RECOMMENDED_VOICES

load_dotenv()

# إعدادات صفحة Streamlit
st.set_page_config(
    page_title="MedHelper | الشرح الطبي الأكاديمي",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص CSS للغة العربية واتجاه النصوص ودعم BiDi
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', sans-serif;
    }
    
    .med-header-card {
        background: linear-gradient(135deg, #102a43 0%, #243b53 100%);
        color: white;
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 25px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.12);
        border-right: 6px solid #38bec9;
    }
    
    .badge-doctor {
        background-color: #38bec9;
        color: #102a43;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# الشريط الجانبي: حالة الاتصال وإعدادات الصوت
with st.sidebar:
    st.image("https://img.icons8.com/color/96/stethoscope.png", width=75)
    st.title("🩺 MedHelper")
    st.caption("نظام الشرح الطبي الأكاديمي الذكي")
    
    # التحقق من مفتاح API
    saved_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "مفتاح Google Gemini API:",
        value=saved_key,
        type="password",
        help="يتم حفظه تلقائياً في ملف .env الآمن بمجلد المشروع"
    )
    
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.success("✅ الذكاء الاصطناعي متصل وجاهز للعمل!")
    else:
        st.warning("⚠️ يرجى إدخال مفتاح Gemini المجاني.")
        st.markdown("[👉 احصل على مفتاحك المجاني في دقيقة من هنا](https://aistudio.google.com/)")

    st.divider()
    st.markdown("### 🎙️ إعدادات الصوت الأكاديمي")
    voice_options = list(RECOMMENDED_VOICES.keys())
    voice_labels = [RECOMMENDED_VOICES[k]["name"] for k in voice_options]
    selected_voice_label = st.selectbox("صوت الشرح الصوتي:", voice_labels, index=0)
    selected_voice_key = voice_options[voice_labels.index(selected_voice_label)]

    st.divider()
    st.markdown("""
    **💡 مميزات المعمارية:**
    - **تكلفة صفرية (100% Free):** بدون أي اشتراكات.
    - **منطق كبار الأساتذة:** تأصيل فسيولوجي، ميكانيزمات دقيقة، لآلئ إكلينيكية، وفخاخ امتحانات.
    """)


# رأس الصفحة الرئيسي
st.markdown("""
<div class="med-header-card">
    <span class="badge-doctor">نواة الشرح الأكاديمي: نموذج د. عبد المتعال فودة</span>
    <h1 style="margin:0; font-size: 2.2rem; color: #ffffff;">منصة MedHelper للشرح الطبي الأكاديمي</h1>
    <p style="margin: 8px 0 0 0; font-size: 1.05rem; color: #d9e2ec; line-height: 1.6;">
        ارفع ملف أي محاضرة طبية (سلايدات أو تفريغ أو مذكرة)، ليقوم النظام بتفكيكها فسيولوجياً وإكلينيكياً، وشرحها لك كما يشرحها كبار الأساتذة المحنكون.
    </p>
</div>
""", unsafe_allow_html=True)


# واجهة المستخدم: خطوة واحدة واضحة
st.subheader("📤 خطوة واحدة: ارفع المحاضرة واحصل على الشرح الأسطوري")

col_upload, col_notes = st.columns([2, 1])

with col_upload:
    upload_type = st.radio(
        "طريقة إدخال المحاضرة:",
        ["رفع ملف (PDF / PowerPoint / TXT)", "كتابة أو لصق نص المحاضرة مباشرة"],
        horizontal=True
    )

with col_notes:
    additional_notes = st.text_input(
        "تركيز خاص مطلوب (اختياري):",
        placeholder="مثال: ركز على أسئلة الامتحانات والـ Clinical Pearls"
    )

lecture_content = ""

if upload_type == "رفع ملف (PDF / PowerPoint / TXT)":
    uploaded_file = st.file_uploader(
        "اختر ملف المحاضرة من جهازك:",
        type=["pdf", "pptx", "ppt", "txt", "md"],
        help="يدعم سلايدات الباوربوينت وملفات الـ PDF والمذكرات النصية"
    )
    if uploaded_file:
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("جاري قراءة واستخراج نصوص المحاضرة..."):
            parse_res = parse_lecture_file(temp_path)
            if parse_res["success"]:
                lecture_content = parse_res["content"]
                st.success(f"✅ تم تحميل المحاضرة بنجاح! ({parse_res.get('total_pages', 1)} صفحات/سلايدات — {parse_res.get('word_count', 0)} كلمة)")
                with st.expander("👁️ استعراض النص المستخرج من المحاضرة"):
                    st.text_area("النص المستخرج:", lecture_content[:2000] + ("..." if len(lecture_content) > 2000 else ""), height=150)
            else:
                st.error(parse_res["error"])
else:
    lecture_content = st.text_area(
        "الصق محتوى المحاضرة أو السلايدات هنا:",
        height=220,
        placeholder="الصق نصوص السلايدات أو النقاط الطبية المراد شرحها بالتفصيل..."
    )

st.write("")
explain_btn = st.button("🚀 اشرح المحاضرة بأسلوب د. عبد المتعال فودة الأكاديمي", type="primary", use_container_width=True)

if explain_btn:
    if not os.getenv("GEMINI_API_KEY"):
        st.error("❌ يرجى التأكد من كتابة مفتاح Google Gemini API في القائمة الجانبية أولاً.")
    elif not lecture_content or len(lecture_content.strip()) < 30:
        st.warning("⚠️ يرجى رفع ملف المحاضرة أو لصق نصها للبدء في الشرح.")
    else:
        with st.spinner("جاري صياغة الشرح الأكاديمي المتعمق وفق الركائز الـ 11 (تأصيل فسيولوجي، ميكانيزمات، لآلئ سريرية)... يرجى الانتظار"):
            res = explain_lecture(
                lecture_text=lecture_content,
                additional_notes=additional_notes
            )

            if res["success"]:
                st.session_state["active_explanation"] = res["explanation"]
                st.session_state["active_audio_script"] = res.get("audio_script", res["explanation"][:1000])
                st.session_state["audio_path"] = None  # إعادة تعيين الصوت للمحاضرة الجديدة
                st.success("🎉 تم توليد المحاضرة بنجاح! يمكنك الاستماع إليها صوتياً الآن.")
            else:
                st.error(res["error"])

# عرض المحاضرة الصوتية أولاً ثم الشرح التفصيلي
if "active_explanation" in st.session_state:
    st.divider()

    # =========================================================================
    # 🎧 ركن الاستماع الصوتي أولاً (Audio-First Experience)
    # =========================================================================
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1f3a52 0%, #172c3c 100%); padding: 18px 22px; border-radius: 12px; border-right: 5px solid #38bec9; margin-bottom: 20px;">
        <h3 style="margin:0; color: #ffffff; font-size: 1.3rem;">🎙️ ركن الاستماع الصوتي (دكتور عبد المتعال فودة)</h3>
        <p style="margin: 5px 0 0 0; color: #cbd5e1; font-size: 0.95rem;">
            استمع للشرح الأكاديمي بصوت طبيعي ونقي، مصمم خصيصاً للأذن لترسيخ الفهم والميكانيزمات وفخاخ الامتحان.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        fast_audio_btn = st.button("⚡ تشغيل المحاضرة الصوتية المركزة (سريعة ومباشرة)", type="primary", use_container_width=True)

    with col_btn2:
        full_audio_btn = st.button("🎧 تشغيل الشرح التفصيلي الكامل بالصوت", use_container_width=True)

    # معالجة توليد الصوت السريع
    if fast_audio_btn:
        with st.spinner("جاري تحويل المحاضرة إلى صوت أكاديمي نقي (يستغرق ثوانٍ معدودة)..."):
            script_to_speak = st.session_state.get("active_audio_script", st.session_state["active_explanation"][:1000])
            audio_res = generate_audio(
                text=script_to_speak,
                output_filename="lecture_podcast.mp3",
                voice_key=selected_voice_key,
                rate="+15%"
            )
            if audio_res["success"]:
                st.session_state["audio_path"] = audio_res["file_path"]
                st.session_state["audio_type"] = "المحاضرة الصوتية المركزة"
            else:
                st.error(audio_res["error"])

    # معالجة توليد الشرح الكامل
    if full_audio_btn:
        with st.spinner("جاري تحويل الشرح التفصيلي الكامل إلى ملف صوتي شامل..."):
            audio_res = generate_audio(
                text=st.session_state["active_explanation"],
                output_filename="lecture_full.mp3",
                voice_key=selected_voice_key,
                rate="+15%"
            )
            if audio_res["success"]:
                st.session_state["audio_path"] = audio_res["file_path"]
                st.session_state["audio_type"] = "الشرح التفصيلي الكامل"
            else:
                st.error(audio_res["error"])

    # مشغل الصوت التفاعلي الثابت
    if st.session_state.get("audio_path") and os.path.exists(st.session_state["audio_path"]):
        st.success(f"✅ تم تجهيز {st.session_state.get('audio_type', 'الصوت')} بنجاح! اضغط تشغيل:")
        st.audio(st.session_state["audio_path"], format="audio/mp3", autoplay=True)

    st.divider()

    # =========================================================================
    # 📋 الشرح المرجعي المكتوب والرسوم التوضيحية
    # =========================================================================
    with st.expander("📖 عرض نص الشرح المرجعي والمخططات الذهنية (اضغط للقراءة)", expanded=True):
        st.markdown(st.session_state["active_explanation"], unsafe_allow_html=True)
        st.write("")
        st.download_button(
            label="📥 تحميل الشرح كملف نصي (Markdown)",
            data=st.session_state["active_explanation"],
            file_name="medical_lecture_explanation.md",
            mime="text/markdown",
            use_container_width=True
        )
