import streamlit as st
import openai

# ====== تنظیمات اولیه ======
st.set_page_config(page_title="دستیار همه‌فن‌حریف", page_icon="🤖")
st.title("🤖 دستیار همه‌فن‌حریف من")

# دریافت کلید API کاربر
api_key = st.text_input("🔑 لطفاً کلید API OpenAI خود را وارد کن:", type="password")
if not api_key:
    st.warning("برای شروع، کلید API رو وارد کن.")
    st.stop()

openai.api_key = api_key

# ====== شخصیت سیستم ======
system_prompt = """تو یک دستیار همه‌فن‌حریف و فوق‌حرفه‌ای هستی با تخصص‌های زیر که هر کدام را در بالاترین سطح بلدی. در پاسخ‌هایت بنا به نیاز از یک یا چند تخصص استفاده کن. دقیق، علمی، کاربردی و دوستانه باش.

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
- استاد جوجیتسو برزیلی (بهترین بی‌رقیب)
- نویسنده
- یخچال‌ساز
- تعمیرکار لباسشویی
- تعمیرکار ماشین ظرفشویی
- مربی بدنسازی
- جامعه‌ساز پُرتجربه

نحوهٔ پاسخ:
- اول با ایموجی و نام تخصصت شروع کن (مثلاً 🏗️ مهندس ساختمان).
- مثل رفیق مشتی صمیمی باش ولی دقت علمی رو حفظ کن.
- اگر سؤالی خارج از تخصص‌ها بود، تلاش کن کمک کنی وگرنه صادقانه بگو تخصص نداری."""

# ====== تاریخچهٔ گفتگو ======
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# نمایش تاریخچه
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])

# دریافت پیام کاربر
if prompt := st.chat_input("سؤالت را اینجا بنویس..."):
    # اضافه کردن پیام کاربر
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # گرفتن پاسخ از OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",   # می‌تونی gpt-4 رو هم بذاری
            messages=st.session_state.messages,
            temperature=0.7,
            max_tokens=1000
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)
    except Exception as e:
        st.error(f"خطا: {e}")
