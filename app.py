# -*- coding: utf-8 -*-
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="دستیار همه‌فن‌حریف رایگان", page_icon="🤖")
st.title("🤖 دستیار همه‌فن‌حریف (رایگان با Groq)")

# کلید Groq
api_key = st.text_input("🔑 کلید API رایگان Groq را وارد کن (gsk_...):", type="password")
if not api_key:
    st.warning("کلید Groq را وارد کن. از console.groq.com بگیر.")
    st.stop()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key
)

# مدل‌های رایگان معتبر در حال حاضر (تیر ۱۴۰۵ / جولای ۲۰۲۶)
model_name = st.selectbox(
    "مدل:",
    [
        "llama-3.1-8b-instant",        # سریع، جایگزین llama-3.2
        "mixtral-8x7b-32768",          # قدرتمند
        "gemma2-9b-it",                # گوگل
        "llama-3.3-70b-versatile",     # بزرگ ولی رایگان
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

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])

if prompt := st.chat_input("سؤالت را اینجا بنویس..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

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
