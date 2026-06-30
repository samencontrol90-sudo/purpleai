# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import subprocess
import tempfile
import os
import json
import base64
from PIL import Image
import io

st.set_page_config(page_title="دستیار همه‌فن‌حریف", page_icon="🤖")
st.title("🤖 دستیار همه‌فن‌حریف (مکالمه صوتی + تصویر)")

# ========== API و مدل ==========
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
        "llama-3.2-11b-vision-preview",  # مدل بینایی (پیش‌فرض برای پشتیبانی از عکس)
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "llama-3.3-70b-versatile",
    ],
    index=0
)

voice_mode = st.toggle("🎙️ مکالمه صوتی (پاسخ‌ها خودکار خوانده شوند)", value=True)

SYSTEM_PROMPT = """تو یک دستیار همه‌فن‌حریف و فوق‌حرفه‌ای هستی که به‌ازای هر سؤال، دقیقاً یک تخصص از میان تخصص‌های زیر را انتخاب می‌کنی و از دید همان متخصص پاسخ می‌دهی. هرگز چند تخصص را با هم ترکیب نکن. برای هر سؤال جدید، دوباره تخصص مناسب را برگزین و تخصص قبلی را فراموش کن. اگر سؤال به هیچ‌یک از تخصص‌هایت مربوط نبود، مؤدبانه بگو در آن زمینه تخصص نداری و راهنمایی جایگزین بده.
اگر کاربر تصویری ارسال کرد، می‌توانی محتوای آن را تحلیل کنی و بر اساس آن پاسخ دهی.

لیست تخصص‌ها (همیشه یکی را انتخاب کن):
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

شیوهٔ پاسخ‌دهی:
- ابتدا خودت را با ایموجی و نام تخصص انتخاب‌شده معرفی کن (مثلاً 🏗️ مهندس ساختمان).
- سپس پاسخی دقیق، علمی و در عین حال خودمونی (رفیق مشتی) ارائه بده.
- هرگز در یک پاسخ چند تخصص را هم‌زمان به کار نبر.
- اگر سؤال جدید کاملاً بی‌ربط با تخصص قبلی بود، بدون اشاره به پاسخ قبلی، تخصص جدید را برگزین."""

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# ========== توابع ==========
def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return None
    file_type = uploaded_file.type
    try:
        if file_type.startswith("text/plain"):
            return uploaded_file.read().decode("utf-8")
        elif file_type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            return None  # برای عکس‌ها
    except Exception as e:
        st.error(f"خطا در خواندن فایل: {e}")
        return None

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

def text_to_speech(text):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        path = tmp.name
    try:
        subprocess.run(
            ["edge-tts", "--voice", "fa-IR-FaridNeural", "--text", text, "--write-media", path],
            check=True, capture_output=True, text=True
        )
        return path
    except subprocess.CalledProcessError as e:
        st.error(f"خطا در ساخت صدا: {e.stderr}")
        return None

def autoplay_audio(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay style="display:none">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)

# ========== تاریخچه ==========
col1, col2 = st.columns(2)
with col1:
    if st.button("📥 دانلود تاریخچه"):
        chat_data = [msg for msg in st.session_state.messages if msg["role"] != "system"]
        st.download_button(
            "💾 ذخیره فایل JSON",
            data=json.dumps(chat_data, ensure_ascii=False, indent=2),
            file_name="chat_history.json",
            mime="application/json"
        )
with col2:
    uploaded_hist = st.file_uploader("📂 بارگذاری تاریخچه (JSON)", type=["json"], key="hist_upload")
    if uploaded_hist is not None:
        try:
            loaded = json.load(uploaded_hist)
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}] + loaded
            st.success("تاریخچه بارگذاری شد!")
            st.rerun()
        except Exception as e:
            st.error(f"خطا: {e}")

# ========== ورودی‌ها ==========
# آپلود فایل (پشتیبانی از عکس و متن – چندتایی)
uploaded_files = st.file_uploader(
    "📎 فایل ضمیمه (txt, pdf, docx, jpg, png) - می‌تونی چندتا انتخاب کنی",
    type=["txt", "pdf", "docx", "jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# ورودی صوتی
col_audio, col_text = st.columns([1, 3])
with col_audio:
    audio_value = st.audio_input("🎤 بگو")
with col_text:
    user_text = ""

    if audio_value is not None:
        with st.spinner("🧠 تشخیص گفتار..."):
            audio_bytes = audio_value.getvalue() if hasattr(audio_value, "getvalue") else audio_value.read()
            user_text = transcribe_audio(audio_bytes)
            if user_text:
                st.success(f"شنیدم: {user_text}")

    prompt = st.chat_input("پیام متنی...") if not user_text else None

if user_text or prompt:
    final_input = user_text if user_text else prompt
    user_content = []

    # اگر فایل آپلود شده باشد
    if uploaded_files:
        for file in uploaded_files:
            file_type = file.type
            # عکس‌ها
            if file_type in ["image/jpeg", "image/png", "image/jpg"]:
                # نمایش عکس
                image = Image.open(file)
                st.image(image, caption=file.name, width=200)
                # تبدیل به base64 برای ارسال به مدل
                file.seek(0)
                img_bytes = file.read()
                img_b64 = base64.b64encode(img_bytes).decode()
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{file_type};base64,{img_b64}"}
                })
            else:
                # فایل متنی: استخراج متن و اضافه کردن به عنوان متن
                file.seek(0)
                text = extract_text_from_file(file)
                if text:
                    # متن را به صورت جداگانه به کاربر نشان نمی‌دهیم، ولی به پرامپت اضافه می‌کنیم
                    user_content.append({
                        "type": "text",
                        "text": f"[محتوای فایل {file.name}]\n{text}"
                    })
    # اضافه کردن متن سوال
    user_content.append({"type": "text", "text": final_input})

    # ساخت پیام کاربر
    st.session_state.messages.append({"role": "user", "content": user_content})

# ========== نمایش تاریخچه ==========
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user"):
            # اگر محتوای چندبخشی (لیست) باشد
            if isinstance(msg["content"], list):
                for item in msg["content"]:
                    if item["type"] == "text":
                        st.write(item["text"])
                    elif item["type"] == "image_url":
                        # نمایش تصویر از base64
                        img_data = item["image_url"]["url"].split(",")[1]
                        st.image(base64.b64decode(img_data))
            else:
                st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])

# ========== تولید پاسخ + پخش صوتی خودکار ==========
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("🤔 در حال فکر کردن..."):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                reply = response.choices[0].message.content
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

                if voice_mode:
                    with st.spinner("🔊 گوینده..."):
                        audio_path = text_to_speech(reply)
                        if audio_path:
                            autoplay_audio(audio_path)
            except Exception as e:
                st.error(f"خطا: {e}")
