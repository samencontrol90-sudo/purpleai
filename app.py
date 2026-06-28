import streamlit as st
import requests
import os
import time
import re

st.set_page_config(page_title="Purple AI", page_icon="🟣", layout="wide")

# احراز هویت
if "auth" not in st.session_state:
    st.session_state.auth = False
if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;color:#9b59b6;'>🟣 Purple AI</h1>", unsafe_allow_html=True)
    pwd = st.text_input("رمز عبور", type="password")
    if st.button("ورود"):
        if pwd == os.getenv("PASSWORD"):
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("رمز اشتباه!")
    st.stop()

# طراحی ظاهری
st.markdown("""<style>
.logo-circle {width:80px;height:80px;border-radius:50%;background:#9b59b6;display:flex;align-items:center;justify-content:center;font-size:40px;color:white;font-weight:bold;font-family:Arial;margin:20px auto;box-shadow:0 4px 15px rgba(155,89,182,0.4);}
</style><div class="logo-circle">C</div><h1 style='text-align:center;color:#6a1b9a;'>Purple AI</h1><hr>""", unsafe_allow_html=True)

menu = st.sidebar.radio("وظیفه", [
    "💬 چت", "🖼️ عکس", "🌍 ترجمه", "🎥 ویدیو",
    "🏥 پزشکی", "🛡️ نظامی", "🔍 جستجوی وب",
    "🛒 فروشگاه", "👨‍💻 مهندس IT"
])

# ========== توابع کمکی ==========
def hf_api(model, data, is_binary=False):
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        if r.status_code == 200:
            return r.content if is_binary else r.json()
    except:
        pass
    return None

def is_persian(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

def translate(text, src, tgt):
    model_map = {
        ("fa", "en"): "Helsinki-NLP/opus-mt-fa-en",
        ("en", "fa"): "Helsinki-NLP/opus-mt-en-fa"
    }
    model = model_map.get((src, tgt), "Helsinki-NLP/opus-mt-en-fa")
    res = hf_api(model, {"inputs": text})
    if res and isinstance(res, list):
        return res[0]['translation_text']
    return text  # fallback

# ========== بخش‌ها ==========
if menu == "💬 چت":
    st.subheader("چت با Purple AI")
    if "msgs" not in st.session_state: st.session_state.msgs = []
    u = st.text_input("شما:")
    if st.button("ارسال") and u:
        st.session_state.msgs.append(("👤", u))
        res = hf_api("microsoft/DialoGPT-small", {"inputs": u})
        if res and isinstance(res, list) and 'generated_text' in res[0]:
            reply = res[0]['generated_text'].replace(u, "").strip()
        else:
            reply = "خطا در دریافت پاسخ"
        st.session_state.msgs.append(("🤖", reply))
    for s, m in st.session_state.msgs: st.markdown(f"**{s}** {m}")

elif menu == "🖼️ عکس":
    st.subheader("تشخیص عکس")
    up = st.file_uploader("عکس", type=["jpg","png","jpeg"])
    if up:
        st.image(up, use_column_width=True)
        with st.spinner("تحلیل..."):
            r = requests.post("https://api-inference.huggingface.co/models/microsoft/resnet-50",
                              headers={"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"},
                              files={"file": up.getvalue()})
            if r.status_code == 200:
                for pred in r.json()[:3]:
                    st.write(f"{pred['label']}: {pred['score']:.2%}")
            else:
                st.error("خطا در تحلیل عکس")

elif menu == "🌍 ترجمه":
    st.subheader("ترجمه هوشمند")
    txt = st.text_area("متن:")
    if st.button("ترجمه") and txt:
        if is_persian(txt):
            out = translate(txt, "fa", "en")
            st.success("فارسی → انگلیسی")
        else:
            out = translate(txt, "en", "fa")
            st.success("انگلیسی → فارسی")
        st.write(out)

elif menu == "🎥 ویدیو":
    st.subheader("تولید ویدیو")
    prompt = st.text_input("صحنه (انگلیسی)")
    if st.button("ساخت") and prompt:
        with st.spinner("۳-۵ دقیقه صبر..."):
            vid = hf_api("ali-vilab/modelscope-damo-text-to-video-synthesis",
                         {"inputs": prompt, "options": {"wait_for_model": True}},
                         is_binary=True)
            if isinstance(vid, bytes):
                fname = f"video_{int(time.time())}.mp4"
                with open(fname, "wb") as f: f.write(vid)
                st.video(fname)
                st.download_button("دانلود", open(fname,"rb"), file_name=fname)
            else:
                st.error("ساخت ویدیو با خطا مواجه شد")

elif menu == "🏥 پزشکی":
    st.subheader("🩺 مشاورهٔ پزشکی (آموزشی)")
    st.warning("⚠️ فقط آموزشی. به پزشک مراجعه کنید.")
    topics = {
        "دیابت": "Type 2 diabetes is a chronic condition that affects the way the body processes blood sugar...",
        "فشار خون": "Hypertension is a condition in which the force of the blood against the artery walls is too high...",
        "کرونا": "COVID-19 is an infectious disease caused by the SARS-CoV-2 virus...",
        "سرماخوردگی": "The common cold is a viral infection of the nose and throat..."
    }
    topic = st.selectbox("موضوع", list(topics.keys()))
    ctx = topics[topic]
    st.markdown(f"**متن مرجع:** {ctx}")
    q = st.text_input("سوال:")
    if st.button("پاسخ") and q:
        if is_persian(q): q = translate(q, "fa", "en")
        ans = hf_api("ktrapeznikov/biobert_v1.1_pubmed_squad_v2", {"question": q, "context": ctx})
        if ans and 'answer' in ans:
            st.write(ans['answer'])
            st.caption(f"امتیاز: {ans['score']:.2%}")
        else:
            st.error("خطا در دریافت پاسخ")

elif menu == "🛡️ نظامی":
    st.subheader("🛡️ تحلیل استراتژیک (آموزشی)")
    topics = {
        "جنگ هیبریدی": "Hybrid warfare blends conventional...",
        "پدافند غیرعامل": "Passive defense refers to measures...",
        "فناوری‌های نوظهور": "Emerging defense technologies...",
        "بازدارندگی": "Deterrence strategy aims to prevent..."
    }
    topic = st.selectbox("موضوع", list(topics.keys()))
    ctx = topics[topic]
    st.markdown(f"**متن مرجع:** {ctx}")
    q = st.text_input("سوال:")
    if st.button("تحلیل") and q:
        if is_persian(q): q = translate(q, "fa", "en")
        ans = hf_api("distilbert-base-cased-distilled-squad", {"question": q, "context": ctx})
        if ans and 'answer' in ans:
            st.write(ans['answer'])
            st.caption(f"امتیاز: {ans['score']:.2%}")
        else:
            st.error("خطا در تحلیل")

elif menu == "🔍 جستجوی وب":
    st.subheader("جستجوی وب با Google")
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")
    if not api_key or not cx:
        st.error("کلیدهای Google API در Secrets تنظیم نشده.")
    else:
        q = st.text_input("عبارت جستجو:")
        if st.button("جستجو") and q:
            r = requests.get("https://www.googleapis.com/customsearch/v1",
                             params={"key": api_key, "cx": cx, "q": q, "num": 5})
            if r.status_code == 200:
                for item in r.json().get("items", []):
                    st.markdown(f"**{item['title']}**  \n{item['snippet']}  \n[{item['link']}]({item['link']})")
                    st.divider()
            else:
                st.error("خطا در جستجو")

elif menu == "🛒 فروشگاه":
    st.subheader("فروشگاه آزمایشی")
    if "cart" not in st.session_state: st.session_state.cart = []
    products = {"هدفون بی‌سیم": 350000, "کتاب پایتون": 120000, "اشتراک VPN": 90000}
    c1, c2 = st.columns(2)
    with c1:
        for name, price in products.items():
            st.write(f"- {name}: {price:,} تومان")
    with c2:
        choice = st.selectbox("محصول", list(products.keys()))
        if st.button("افزودن به سبد"):
            st.session_state.cart.append((choice, products[choice]))
            st.success("اضافه شد")
    if st.session_state.cart:
        total = sum(p for _, p in st.session_state.cart)
        for item, price in st.session_state.cart:
            st.write(f"- {item}: {price:,} تومان")
        st.write(f"**جمع: {total:,} تومان**")
        if st.button("ثبت سفارش (آزمایشی)"):
            st.balloons()
            st.success("سفارش ثبت شد (شبیه‌سازی)")
            st.session_state.cart = []

elif menu == "👨‍💻 مهندس IT":
    st.subheader("👨‍💻 مهندس IT")
    issues = {
        "وای‌فای قطع شده": "WiFi keeps disconnecting on Windows 11",
        "کندی ویندوز": "Windows 10 running very slow, how to speed up",
        "نصب پایتون": "How to install Python on Windows 11",
        "ارور 404": "What does HTTP 404 error mean and how to fix",
        "پرینتر": "Printer not responding, troubleshooting steps"
    }
    col1, col2 = st.columns([1,2])
    with col1:
        selected = st.selectbox("مشکلات رایج:", ["(انتخاب کنید)"] + list(issues.keys()))
    with col2:
        free_q = st.text_input("یا سوالت رو مستقیم بنویس:")
    if st.button("کمک بگیر"):
        if selected != "(انتخاب کنید)":
            q = issues[selected]
        elif free_q:
            q = free_q
        else:
            st.warning("لطفاً یک مشکل انتخاب یا تایپ کن.")
            st.stop()
        if is_persian(q): q = translate(q, "fa", "en")
        prompt = "You are a skilled IT engineer. Answer helpfully: " + q
        res = hf_api("microsoft/DialoGPT-small", {"inputs": prompt})
        if res and isinstance(res, list) and 'generated_text' in res[0]:
            ans = res[0]['generated_text'].replace(prompt, "").strip()
        else:
            ans = "خطا در دریافت پاسخ"
        st.write(ans)
