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

st.set_page_config(page_title="دستیار همه‌فن‌حریف", page_icon="🤖")
st.title("🤖 دستیار همه‌فن‌حریف (رایگان + مکالمه صوتی)")

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
    ["llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it", "llama-3.3-70b-versatile"],
    index=0
)

# حالت گفتگوی صوتی
voice_mode = st.checkbox("🎙️ حالت گفتگوی صوتی (بدون نیاز به کلیک برای شنیدن پاسخ)")

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

if "audio_cache" not in st.session_state:
    st.session_state.audio_cache = {}

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

def text_to_speech(text):
    """ساخت فایل صوتی با edge-tts (صدای فرید فارسی)"""
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
    """پخش خودکار صدا با HTML5 (در حالت گفتگوی صوتی)"""
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay controls style="display:none">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)

# ==================== تاریخچه چت ====================
col1, col2 = st.columns(2)
with col1:
    if st.button("📥 دانلود تاریخچه"):
        chat_data = [msg for msg in st.session_state.messages if msg["role"] != "system"]
        st.download_button(
            label="💾 کلیک کن و ذخیره کن",
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
            st.success("تاریخچه با موفقیت بارگذاری شد!")
            st.rerun()
        except Exception as e:
            st.error(f"خطا در بارگذاری: {e}")

# ==================== ورودی‌ها ====================
uploaded_file = st.file_uploader("📎 فایل ضمیمه (txt, pdf, docx)", type=["txt", "pdf", "docx"])

audio_value = st.audio_input("🎤 سؤال صوتی (صحبت کن)")
user_text = ""

if audio_value is not None:
    with st.spinner("در حال تبدیل صوت به متن..."):
        audio_bytes = audio_value.getvalue() if hasattr(audio_value, "getvalue") else audio_value.read()
        user_text = transcribe_audio(audio_bytes)
        if user_text:
            st.success(f"متن تشخیص داده شد: {user_text}")

prompt = st.chat_input("سؤالت را اینجا بنویس...") if not user_text else None

if user_text or prompt:
    final_input = user_text if user_text else prompt
    if uploaded_file is not None:
        file_content = extract_text_from_file(uploaded_file)
        if file_content:
            final_input = f"محتوای فایل ضمیمه:\n{file_content}\n\nسؤال کاربر:\n{final_input}"
    st.session_state.messages.append({"role": "user", "content": final_input})

# ==================== نمایش تاریخچه ====================
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])
            # در حالت صوتی دکمه جدا نمی‌خواهیم، اما اگر کاربر خواست دستی گوش دهد، می‌تواند
            if not voice_mode:
                if st.button("🔊 خواندن پاسخ", key=f"speak_{i}"):
                    if i not in st.session_state.audio_cache:
                        with st.spinner("در حال ساخت صدا..."):
                            path = text_to_speech(msg["content"])
                            if path:
                                st.session_state.audio_cache[i] = path
                    if i in st.session_state.audio_cache:
                        st.audio(st.session_state.audio_cache[i], format="audio/mp3")

# ==================== تولید پاسخ ====================
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
                st.session_state.messages.append({"role": "assistant", "content": reply})

                # اگر حالت گفتگوی صوتی فعال باشد، بلافاصله صدا ساخته و پخش شود
                if voice_mode:
                    with st.spinner("🔊 در حال خواندن پاسخ..."):
                        audio_path = text_to_speech(reply)
                        if audio_path:
                            autoplay_audio(audio_path)
                            # نگهداری در کش برای استفاده بعدی
                            idx = len(st.session_state.messages) - 1
                            st.session_state.audio_cache[idx] = audio_path
            except Exception as e:
                st.error(f"خطا: {e}")
