# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import tempfile
import os
from gtts import gTTS
import json

st.set_page_config(page_title="دستیار همه‌فن‌حریف", page_icon="🤖")
st.title("🤖 دستیار همه‌فن‌حریف (رایگان + صوتی + تاریخچه)")

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

SYSTEM_PROMPT = """تو یک دستیار همه‌فن‌حریف و فوق‌حرفه‌ای هستی با تخصص‌های زیر ..."""  # (کاملش رو قبلاً نوشتی، همون رو بذار)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# ==================== توابع کمکی ====================

def extract_text_from_file(uploaded_file):
    # (همان کد قبلی)
    ...

def transcribe_audio(audio_bytes):
    # (همان کد قبلی با Groq Whisper)
    ...

def text_to_speech(text):
    """تولید فایل صوتی با gTTS"""
    tts = gTTS(text=text, lang='fa', slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts.save(tmp.name)
        return tmp.name

# ==================== تاریخچه چت (دانلود/بارگذاری) ====================
col1, col2 = st.columns(2)
with col1:
    # دکمه دانلود تاریخچه
    if st.button("📥 دانلود تاریخچه"):
        chat_history = [msg for msg in st.session_state.messages if msg["role"] != "system"]
        json_str = json.dumps(chat_history, ensure_ascii=False, indent=2)
        st.download_button(
            label="کلیک کن و فایل را ذخیره کن",
            data=json_str,
            file_name="chat_history.json",
            mime="application/json"
        )
with col2:
    # بارگذاری تاریخچه
    uploaded_history = st.file_uploader("📂 بارگذاری تاریخچه (JSON)", type=["json"])
    if uploaded_history is not None:
        try:
            loaded = json.load(uploaded_history)
            # جایگزینی پیام‌ها (سیستم پرامپت حفظ می‌شود)
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}] + loaded
            st.success("تاریخچه بارگذاری شد!")
            st.rerun()
        except Exception as e:
            st.error(f"خطا در بارگذاری: {e}")

# ==================== بخش آپلود فایل ====================
uploaded_file = st.file_uploader("📎 فایل ضمیمه", type=["txt", "pdf", "docx"])

# ==================== ورودی صوتی ====================
audio_value = st.audio_input("🎤 سؤال صوتی")
user_text = ""
if audio_value is not None:
    with st.spinner("در حال تبدیل صوت..."):
        audio_bytes = audio_value.getvalue() if hasattr(audio_value, "getvalue") else audio_value.read()
        user_text = transcribe_audio(audio_bytes)
        if user_text:
            st.success(f"متن: {user_text}")

# ==================== ورودی متنی ====================
prompt = st.chat_input("سؤالت را اینجا بنویس...") if not user_text else None

if user_text or prompt:
    final_input = user_text if user_text else prompt
    if uploaded_file:
        file_content = extract_text_from_file(uploaded_file)
        if file_content:
            final_input = f"محتوای فایل:\n{file_content}\n\nسؤال:\n{final_input}"
    st.session_state.messages.append({"role": "user", "content": final_input})

# ==================== نمایش تاریخچه و دکمه صوتی ====================
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])
            if st.button("🔊 خواندن پاسخ", key=f"speak_{i}"):
                with st.spinner("در حال ساخت صدا..."):
                    audio_path = text_to_speech(msg["content"])
                    st.audio(audio_path, format="audio/mp3")
                    os.unlink(audio_path)

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
            except Exception as e:
                st.error(f"خطا: {e}")
