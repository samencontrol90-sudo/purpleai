import streamlit as st
import openai

# ====== تنظیمات صفحه ======
st.set_page_config(page_title="دستیار همه‌فن‌حریف", page_icon="🤖")
st.title("🤖 دستیار همه‌فن‌حریف من")

# ====== کلید API ======
api_key = st.text_input("🔑 کلید API OpenAI خود را وارد کن:", type="password")
if not api_key:
    st.warning("برای شروع گفتگو، کلید API را وارد کن.")
    st.stop()

openai.api_key = api_key

# ====== پرامپت سیستم (شخصیت چندتخصصه) ======
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

# ====== مدیریت تاریخچه‌ی گفتگو ======
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# نمایش تاریخچه
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.write(msg["content"])

# ====== دریافت سؤال کاربر ======
if prompt := st.chat_input("سؤالت را اینجا بنویس..."):
    # پیام کاربر
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # دریافت پاسخ از OpenAI
    with st.chat_message("assistant"):
        with st.spinner("در حال فکر کردن..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",   # می‌تونی gpt-4 هم بذاری
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                reply = response.choices[0].message.content
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"خطا در ارتباط با OpenAI: {e}")
