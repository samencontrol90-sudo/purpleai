# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import io
import json
import PyPDF2
import docx

st.set_page_config(page_title="دستیار همه‌فن‌حریف رایگان", page_icon="🤖")
st.title("🤖 دستیار همه‌فن‌حریف (رایگان با Groq)")

# ==================== تنظیمات اولیه ====================

api_key = st.text_input("🔑 کلید API رایگان Groq را وارد کن (gsk_...):", type="password")
if not api_key:
    st.warning("کلید Groq را وارد کن. از console.groq.com بگیر.")
    st.stop()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key
)

model_name = st.selectbox(
    "مدل:",
    [
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "llama-3.3-70b-versatile",
    ],
    index=0
)

SYSTEM_PROMPT = """تو یک دستیار همه‌فن‌حریف و فوق‌حرفه‌ای هستی با تخصص‌های زیر که هر کدام را در بالاترین سطح بلدی. در پاسخ‌هایت بنا به نیاز از یک یا چند تخصص استفاده کن. دقیق، علمی، کاربردی و دوستانه باش.

لیست تخصص‌ها:
- مهندس برق صنعتی
- آشپز حرفه‌ای
- کارشناس طلا و ارز
- مهندس حرفه‌ای الکترونیک
- مهندس ساختمان حرفه‌ای و پرسابقه
- کشاورز حرفه‌ای
- گل‌شناس آپارتمانی
- جانورشناس
- روانشناس
- کارشناس دینی حرفه‌ای و مجتهد
- پوسترساز حرفه‌ای
- ادیتور حرفه‌ای
- گوشی‌شناس حرفه‌ای
- درخت‌شناس حرفه‌ای
- رفیق مشتی
- مخترع حرفه‌ای
- کتابخوان حرفه‌ای
- کوهنورد حرفه‌ای
- دوچرخه‌سوار پُرتجربه
- استاد جوجیتسو برزیلی (بهترینِ بی‌رقیب)
- نویسنده
- یخچال‌ساز
- تعمیرکار لباسشویی
- تعمیرکار ماشین ظرفشویی
- مربی بدنسازی
- جامعه‌ساز پُرتجربه

نحوه‌ی پاسخ:
- اول با ایموجی و نام تخصص مربوطه شروع کن (مثلاً 🏗️ مهندس ساختمان).
- مثل یه رفیق مشتی صمیمی باش ولی دقت علمی را حفظ کن.
- اگر سؤالی خارج از تخصص‌ها بود، تلاش کن کمک کنی وگرنه صادقانه بگو تخصص نداری."""

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# ==================== تعریف توابع کمکی ====================

def extract_text_from_file(uploaded_file):
    """استخراج متن از فایل‌های txt، pdf و docx"""
    if uploaded_file is None:
        return ""
    file_type = uploaded_file.type
    try:
        if file_type == "text/plain":
            return uploaded_file.read().decode("utf-8")
        elif file_type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        else:
            return ""
    except Exception as e:
        st.error(f"خطا در خواندن فایل: {e}")
        return ""

def transcribe_audio(audio_bytes):
    """تبدیل صوت به متن با استفاده از Whisper Groq"""
    try:
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=("audio.wav", audio_bytes, "audio/wav"),
            response_format="text"
        )
        return transcript
    except Exception as e:
        st.error(f"خطا در تبدیل صوت: {e}")
        return ""

# تزریق تابع JavaScript برای خروجی صوتی (فقط یک بار)
st.components.v1.html(
    """
    <script>
    function speakText(txt) {
        var u = new SpeechSynthesisUtterance(txt);
        u.lang = 'fa-IR';
        window.speechSynthesis.speak(u);
    }
    </script>
    """,
    height=0,
)

# ==================== بخش آپلود فایل ====================
uploaded_file = st.file_uploader(
    "📎 فایل ضمیمه (txt, pdf, docx)",
    type=["txt", "pdf", "docx"],
    help="می‌تونی یک فایل متنی یا PDF یا Word آپلود کنی، محتواش ضمیمهٔ سؤالت می‌شه"
)

# ==================== بخش ورودی صوتی ====================
audio_value = st.audio_input("🎤 سؤال صوتی (صحبت کن)")
user_text = ""

if audio_value is not None:
    with st.spinner("در حال تبدیل صوت به متن..."):
        audio_bytes = audio_value.getvalue() if hasattr(audio_value, "getvalue") else audio_value.read()
        user_text = transcribe_audio(audio_bytes)
        if user_text:
            st.success(f"متن تشخیص داده شد: {user_text}")

# ==================== ورودی متنی ====================
# اگر ورودی صوتی وجود داشت، آن را جایگزین متن می‌کنیم
if not user_text:
    prompt = st.chat_input("سؤالت را اینجا بنویس...")
else:
    prompt = None  # چون صوتی داشتیم، متن دستی نمی‌گیریم

# پردازش نهایی ورودی (چه متنی چه صوتی)
if user_text or prompt:
    final_input = user_text if user_text else prompt

    # اگر فایلی آپلود شده بود، محتوایش را به ابتدای سؤال اضافه کن
    if uploaded_file is not None:
        file_content = extract_text_from_file(uploaded_file)
        if file_content:
            final_input = f"محتوای فایل ضمیمه:\n{file_content}\n\nسؤال کاربر:\n{final_input}"

    # اضافه کردن پیام کاربر
    st.session_state.messages.append({"role": "user", "content": final_input})

# ==================== نمایش تاریخچه چت ====================
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])
            # دکمهٔ خروجی صوتی برای هر پاسخ
            safe_text = json.dumps(msg["content"], ensure_ascii=False)
            st.markdown(
                f'<button onclick="speakText({safe_text})">🔊 خواندن پاسخ</button>',
                unsafe_allow_html=True,
            )

# ==================== تولید پاسخ توسط مدل ====================
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("در حال فکر کردن..."):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                reply = response.choices[0].message.content
                st.write(reply)
                # دکمهٔ خواندن برای این پاسخ هم اضافه می‌شه (بعد از نمایش)
                safe_reply = json.dumps(reply, ensure_ascii=False)
                st.markdown(
                    f'<button onclick="speakText({safe_reply})">🔊 خواندن پاسخ</button>',
                    unsafe_allow_html=True,
                )
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"خطا: {e}")
