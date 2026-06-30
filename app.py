# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import io
import json
import PyPDF2
import docx
import edge_tts
import asyncio
import tempfile
import os

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

# ==================== توابع کمکی ====================

def extract_text_from_file(uploaded_file):
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

async def text_to_speech_async(text, voice="fa-IR-FaridNeural"):
    """تبدیل متن به فایل صوتی با edge-tts (نیاز به async)"""
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        await communicate.save(tmp_file.name)
        return tmp_file.name

def text_to_speech(text, voice="fa-IR-FaridNeural"):
    """wrapper همگام برای Streamlit"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(text_to_speech_async(text, voice))
    loop.close()
    return result

# ==================== بخش آپلود فایل ====================
uploaded_file = st.file_uploader(
    "📎 فایل ضمیمه (txt, pdf, docx)",
    type=["txt", "pdf", "docx"],
    help="فایل متنی یا PDF یا Word آپلود کن، محتواش ضمیمهٔ سؤال می‌شه"
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
if not user_text:
    prompt = st.chat_input("سؤالت را اینجا بنویس...")
else:
    prompt = None

if user_text or prompt:
    final_input = user_text if user_text else prompt

    if uploaded_file is not None:
        file_content = extract_text_from_file(uploaded_file)
        if file_content:
            final_input = f"محتوای فایل ضمیمه:\n{file_content}\n\nسؤال کاربر:\n{final_input}"

    st.session_state.messages.append({"role": "user", "content": final_input})

# ==================== نمایش تاریخچه چت ====================
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])
            # دکمهٔ خواندن پاسخ
            if st.button("🔊 خواندن پاسخ", key=f"speak_{i}"):
                with st.spinner("در حال ساخت صدا..."):
                    audio_file = text_to_speech(msg["content"])
                    st.audio(audio_file, format="audio/mp3")
                    # حذف فایل موقت بعد از پخش (اختیاری)
                    try:
                        os.unlink(audio_file)
                    except:
                        pass

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
                # دکمهٔ خواندن برای این پاسخ جدید
                if st.button("🔊 خواندن پاسخ", key=f"speak_new_{len(st.session_state.messages)}"):
                    with st.spinner("در حال ساخت صدا..."):
                        audio_file = text_to_speech(reply)
                        st.audio(audio_file, format="audio/mp3")
                        try:
                            os.unlink(audio_file)
                        except:
                            pass
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"خطا: {e}")
