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
import cv2
import numpy as np
from datetime import timedelta

st.set_page_config(page_title="دستیار همه‌فن‌حریف", page_icon="🤖")
st.title("🤖 دستیار همه‌فن‌حریف (ویرایش ویدیو + مکالمه صوتی)")

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
        "llama-3.2-11b-vision-preview",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "llama-3.3-70b-versatile",
    ],
    index=0
)

voice_mode = st.toggle("🎙️ مکالمه صوتی (پاسخ‌ها خودکار خوانده شوند)", value=True)

SYSTEM_PROMPT = """تو یک دستیار همه‌فن‌حریف و فوق‌حرفه‌ای هستی که به‌ازای هر سؤال، دقیقاً یک تخصص از میان تخصص‌های زیر را انتخاب می‌کنی و از دید همان متخصص پاسخ می‌دهی. هرگز چند تخصص را با هم ترکیب نکن. برای هر سؤال جدید، دوباره تخصص مناسب را برگزین و تخصص قبلی را فراموش کن. اگر سؤال به هیچ‌یک از تخصص‌هایت مربوط نبود، مؤدبانه بگو در آن زمینه تخصص نداری و راهنمایی جایگزین بده.
اگر کاربر تصویری یا فریم‌های ویدیو ارسال کرد، آن‌ها را تحلیل کن و بر اساس آن پاسخ بده.

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

# ========== توابع عمومی ==========
def extract_text_from_file(uploaded_file):
    if uploaded_file is None: return None
    file_type = uploaded_file.type
    try:
        if file_type.startswith("text/plain"): return uploaded_file.read().decode("utf-8")
        elif file_type == "application/pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in reader.pages])
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([para.text for para in docx.Document(uploaded_file).paragraphs])
    except Exception as e:
        st.error(f"خطا در خواندن فایل: {e}")
    return None

def transcribe_audio(audio_bytes):
    try:
        return client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=("audio.wav", audio_bytes, "audio/wav"),
            response_format="text"
        )
    except Exception as e:
        st.error(f"خطا در تبدیل صوت: {e}")
        return ""

def text_to_speech(text):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        path = tmp.name
    try:
        subprocess.run(["edge-tts", "--voice", "fa-IR-FaridNeural", "--text", text, "--write-media", path],
                       check=True, capture_output=True, text=True)
        return path
    except subprocess.CalledProcessError as e:
        st.error(f"خطا در ساخت صدا: {e.stderr}")
        return None

def autoplay_audio(file_path):
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'<audio autoplay style="display:none"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
                    unsafe_allow_html=True)

def preprocess_image(img_bytes, max_dim=512, quality=50):
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        w, h = img.size
        if max(w, h) > max_dim:
            r = max_dim / max(w, h)
            img = img.resize((int(w * r), int(h * r)), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return buf.getvalue()
    except:
        return img_bytes

def extract_video_frames(video_bytes, num_frames=3):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_bytes)
        vpath = tmp.name
    cap = cv2.VideoCapture(vpath)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        os.unlink(vpath); return []
    positions = [int(total * p) for p in [0.25, 0.5, 0.75]]
    frames = []
    for pos in positions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ret, frame = cap.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            buf = io.BytesIO()
            Image.fromarray(rgb).save(buf, format="JPEG", quality=70)
            frames.append(buf.getvalue())
    cap.release()
    os.unlink(vpath)
    return frames

# ========== ویرایش ویدیو با OpenCV ==========
def trim_video(video_bytes, start_sec, end_sec):
    """بُرش بخشی از ویدیو از start_sec تا end_sec (ثانیه)"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_bytes)
        vpath = tmp.name
    cap = cv2.VideoCapture(vpath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    start_frame = max(0, int(start_sec * fps))
    end_frame = min(total_frames, int(end_sec * fps))
    if start_frame >= end_frame:
        cap.release(); os.unlink(vpath); return None, "زمان شروع باید کمتر از پایان باشد."

    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = None
    current = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        if current >= end_frame: break
        if current >= start_frame:
            if out is None:
                h, w = frame.shape[:2]
                out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
            out.write(frame)
        current += 1
    cap.release()
    if out: out.release()
    os.unlink(vpath)
    return out_path, None

def add_text_to_video(video_bytes, text, position="bottom", font_scale=1, color=(255,255,255)):
    """افزودن متن روی تمام فریم‌های ویدیو"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(video_bytes)
        vpath = tmp.name
    cap = cv2.VideoCapture(vpath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    while True:
        ret, frame = cap.read()
        if not ret: break
        # محاسبه موقعیت متن
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
        if position == "top":
            org = (10, th + 10)
        elif position == "center":
            org = ((w - tw) // 2, (h + th) // 2)
        else:  # bottom
            org = (10, h - 20)
        cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)
        out.write(frame)
    cap.release(); out.release()
    os.unlink(vpath)
    return out_path

# ========== تاریخچه ==========
col1, col2 = st.columns(2)
with col1:
    if st.button("📥 دانلود تاریخچه"):
        chat_data = [msg for msg in st.session_state.messages if msg["role"] != "system"]
        st.download_button("💾 ذخیره فایل JSON", data=json.dumps(chat_data, ensure_ascii=False, indent=2),
                           file_name="chat_history.json", mime="application/json")
with col2:
    uploaded_hist = st.file_uploader("📂 بارگذاری تاریخچه (JSON)", type=["json"], key="hist_upload")
    if uploaded_hist:
        try:
            loaded = json.load(uploaded_hist)
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}] + loaded
            st.success("تاریخچه بارگذاری شد!"); st.rerun()
        except Exception as e:
            st.error(f"خطا: {e}")

# ========== بخش اصلی: ورودی و انتخاب حالت ==========
st.subheader("📂 فایل‌های خود را آپلود کنید")
uploaded_files = st.file_uploader(
    "فرمت‌های مجاز: تصویر (jpg,png)، متن (txt,pdf,docx)، ویدیو (mp4,mov,avi)",
    type=["txt","pdf","docx","jpg","jpeg","png","mp4","mov","avi"],
    accept_multiple_files=True
)

# اگر ویدیو آپلود شده، گزینه‌های ویرایش ظاهر شود
edit_video = False
if uploaded_files:
    has_video = any(f.type.startswith("video") for f in uploaded_files)
    if has_video:
        action = st.radio("🎬 عملیات روی ویدیو:", ["تحلیل محتوا", "ویرایش (بُرش / متن)"], index=0)
        if action == "ویرایش (بُرش / متن)":
            edit_video = True

if edit_video and uploaded_files:
    video_file = next(f for f in uploaded_files if f.type.startswith("video"))
    video_bytes = video_file.read()
    st.video(video_bytes)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("✂️ بُرش ویدیو"):
            with st.form("trim_form"):
                start = st.number_input("شروع (ثانیه)", min_value=0.0, value=0.0, step=1.0)
                end = st.number_input("پایان (ثانیه)", min_value=0.0, value=10.0, step=1.0)
                if st.form_submit_button("انجام بُرش"):
                    out_path, err = trim_video(video_bytes, start, end)
                    if err:
                        st.error(err)
                    else:
                        with open(out_path, "rb") as f:
                            st.download_button("⬇️ دانلود ویدیوی برش‌خورده", f, file_name="trimmed.mp4", mime="video/mp4")
                        os.unlink(out_path)
    with col_t2:
        if st.button("📝 درج متن روی ویدیو"):
            with st.form("text_form"):
                user_text = st.text_input("متن مورد نظر", value="متن نمونه")
                pos = st.selectbox("موقعیت متن", ["بالا", "وسط", "پایین"], index=2)
                color_hex = st.color_picker("رنگ متن", "#FFFFFF")
                if st.form_submit_button("اعمال متن"):
                    color_rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                    pos_map = {"بالا": "top", "وسط": "center", "پایین": "bottom"}
                    out_path = add_text_to_video(video_bytes, user_text, pos_map[pos], color=color_rgb)
                    with open(out_path, "rb") as f:
                        st.download_button("⬇️ دانلود ویدیو با متن", f, file_name="text_added.mp4", mime="video/mp4")
                    os.unlink(out_path)

else:   # حالت عادی چت و تحلیل
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
        if uploaded_files:
            for file in uploaded_files:
                ftype = file.type
                if ftype in ["image/jpeg","image/png","image/jpg"]:
                    img = Image.open(file); st.image(img, caption=file.name, width=200)
                    file.seek(0); raw = file.read()
                    optimized = preprocess_image(raw)
                    img_b64 = base64.b64encode(optimized).decode()
                    user_content.append({"type":"image_url", "image_url":{"url":f"data:{ftype};base64,{img_b64}"}})
                elif ftype.startswith("video"):
                    st.video(file)
                    file.seek(0); vb = file.read()
                    frames = extract_video_frames(vb, 3)
                    if frames:
                        cols = st.columns(len(frames))
                        for idx, fb in enumerate(frames):
                            cols[idx].image(fb, caption=f"فریم {idx+1}", width=150)
                            fb_b64 = base64.b64encode(fb).decode()
                            user_content.append({"type":"image_url", "image_url":{"url":f"data:image/jpeg;base64,{fb_b64}"}})
                        user_content.append({"type":"text", "text":"[این فریم‌ها از ویدیوی ارسالی استخراج شده‌اند. محتوای کلی ویدیو را توضیح بده.]"})
                else:
                    file.seek(0); txt = extract_text_from_file(file)
                    if txt:
                        user_content.append({"type":"text", "text":f"[محتوای فایل {file.name}]\n{txt}"})
        user_content.append({"type":"text","text":final_input})
        st.session_state.messages.append({"role":"user","content":user_content})

    # نمایش چت
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            with st.chat_message("user"):
                if isinstance(msg["content"], list):
                    for item in msg["content"]:
                        if item["type"] == "text": st.write(item["text"])
                        elif item["type"] == "image_url":
                            st.image(base64.b64decode(item["image_url"]["url"].split(",")[1]))
                else: st.write(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(msg["content"])

    # تولید پاسخ
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last = st.session_state.messages[-1]["content"]
        has_media = isinstance(last, list) and any(item["type"] == "image_url" for item in last)
        spin = "🧠 تحلیل تصویر..." if has_media else "🤔 فکر کردن..."
        with st.chat_message("assistant"):
            with st.spinner(spin):
                try:
                    resp = client.chat.completions.create(model=model_name, messages=st.session_state.messages,
                                                          temperature=0.7, max_tokens=1000)
                    reply = resp.choices[0].message.content
                    st.write(reply)
                    st.session_state.messages.append({"role":"assistant","content":reply})
                    if voice_mode:
                        with st.spinner("🔊 گوینده..."):
                            apath = text_to_speech(reply)
                            if apath:
                                autoplay_audio(apath)
                except Exception as e:
                    st.error(f"خطا: {e}")
