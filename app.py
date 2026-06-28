import streamlit as st
import requests
import os
import time
from googletrans import Translator

st.set_page_config(page_title="Purple AI", page_icon="🟣", layout="wide")

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

st.markdown("""<style>
.logo-circle {width:80px;height:80px;border-radius:50%;background:#9b59b6;display:flex;align-items:center;justify-content:center;font-size:40px;color:white;font-weight:bold;font-family:Arial;margin:20px auto;box-shadow:0 4px 15px rgba(155,89,182,0.4);}
</style><div class="logo-circle">C</div><h1 style='text-align:center;color:#6a1b9a;'>Purple AI</h1><hr>""", unsafe_allow_html=True)

menu = st.sidebar.radio("وظیفه", ["💬 چت", "🖼️ عکس", "🌍 ترجمه", "🎥 ویدیو", "🏥 پزشکی", "🛡️ نظامی", "🔍 جستجوی وب", "🛒 فروشگاه", "👨‍💻 مهندس IT"])
tr = Translator()

def query_hf(model_name, payload):
    API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            return r.json() if r.headers.get('content-type') != 'video/mp4' else r.content
        else:
            return None
    except:
        return None

# ========== چت ==========
if menu == "💬 چت":
    st.subheader("چت با Purple AI")
    if "msgs" not in st.session_state: st.session_state.msgs = []
    u = st.text_input("شما:")
    if st.button("ارسال") and u:
        st.session_state.msgs.append(("👤", u))
        res = query_hf("microsoft/DialoGPT-small", {"inputs": u})
        reply = res[0]['generated_text'].split(u)[-1].strip() if res and isinstance(res, list) and 'generated_text' in res[0] else "خطا در پاسخ"
        st.session_state.msgs.append(("🤖", reply))
    for s, m in st.session_state.msgs: st.markdown(f"**{s}** {m}")

# ========== عکس ==========
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
                for res in r.json()[:3]: st.write(f"{res['label']}: {res['score']:.2%}")
            else: st.error("خطا در تحلیل عکس")

# ========== ترجمه ==========
elif menu == "🌍 ترجمه":
    st.subheader("ترجمه")
    txt = st.text_area("متن")
    if st.button("ترجمه") and txt:
        det = tr.detect(txt)
        dest = 'en' if det.lang == 'fa' else 'fa'
        res = tr.translate(txt, dest=dest)
        st.success(f"{det.lang} → {dest}: {res.text}")

# ========== ویدیو ==========
elif menu == "🎥 ویدیو":
    st.subheader("تولید ویدیو")
    prompt = st.text_input("صحنه (انگلیسی)")
    if st.button("ساخت") and prompt:
        with st.spinner("۳-۵ دقیقه صبر..."):
            vid = query_hf("ali-vilab/modelscope-damo-text-to-video-synthesis", {"inputs": prompt, "options": {"wait_for_model": True}})
            if isinstance(vid, bytes):
                fname = f"video_{int(time.time())}.mp4"
                with open(fname, "wb") as f: f.write(vid)
                st.video(fname)
                st.download_button("دانلود", open(fname,"rb"), file_name=fname)
            else: st.error("خطا در ساخت ویدیو")

# ========== پزشکی ==========
elif menu == "🏥 پزشکی":
    st.subheader("🩺 مشاورهٔ پزشکی (آموزشی)")
    st.warning("⚠️ فقط آموزشی. به پزشک مراجعه کنید.")
    med = {"دیابت": "Type 2 diabetes is a chronic condition...", "فشار خون": "Hypertension is a condition...", "کرونا": "COVID-19 is an infectious disease...", "سرماخوردگی": "The common cold is a viral infection..."}
    topic = st.selectbox("موضوع", list(med.keys()))
    ctx = med[topic]
    st.markdown(f"**مرجع:** {ctx}")
    q = st.text_input("سوال:")
    if st.button("پاسخ") and q:
        if any('\u0600' <= c <= '\u06FF' for c in q): q = tr.translate(q, dest='en').text
        ans = query_hf("ktrapeznikov/biobert_v1.1_pubmed_squad_v2", {"question": q, "context": ctx})
        st.write(ans['answer'] if ans and 'answer' in ans else "خطا")

# ========== نظامی ==========
elif menu == "🛡️ نظامی":
    st.subheader("🛡️ تحلیل استراتژیک (آموزشی)")
    mil = {"جنگ هیبریدی": "Hybrid warfare blends conventional...", "پدافند غیرعامل": "Passive defense refers...", "فناوری‌های نوظهور": "Emerging defense technologies...", "بازدارندگی": "Deterrence strategy aims..."}
    topic = st.selectbox("موضوع", list(mil.keys()))
    ctx = mil[topic]
    st.markdown(f"**مرجع:** {ctx}")
    q = st.text_input("سوال:")
    if st.button("تحلیل") and q:
        if any('\u0600' <= c <= '\u06FF' for c in q): q = tr.translate(q, dest='en').text
        ans = query_hf("distilbert-base-cased-distilled-squad", {"question": q, "context": ctx})
        st.write(ans['answer'] if ans and 'answer' in ans else "خطا")

# ========== جستجوی وب ==========
elif menu == "🔍 جستجوی وب":
    st.subheader("جستجوی وب با Google")
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")
    if not api_key or not cx: st.error("کلیدهای API در Secrets تنظیم نشده.")
    else:
        q = st.text_input("عبارت:")
        if st.button("جستجو") and q:
            r = requests.get("https://www.googleapis.com/customsearch/v1", params={"key": api_key, "cx": cx, "q": q, "num": 5})
            if r.status_code == 200:
                for item in r.json().get("items", []):
                    st.markdown(f"**{item['title']}**  \n{item['snippet']}  \n[{item['link']}]({item['link']})")
                    st.divider()
            else: st.error("خطا")

# ========== فروشگاه ==========
elif menu == "🛒 فروشگاه":
    st.subheader("فروشگاه آزمایشی")
    if "cart" not in st.session_state: st.session_state.cart = []
    products = {"هدفون بی‌سیم": 350000, "کتاب پایتون": 120000, "اشتراک VPN": 90000}
    c1, c2 = st.columns(2)
    with c1:
        for n, p in products.items(): st.write(f"- {n}: {p:,} تومان")
    with c2:
        choice = st.selectbox("محصول", list(products.keys()))
        if st.button("افزودن به سبد"):
            st.session_state.cart.append((choice, products[choice]))
            st.success("اضافه شد")
    if st.session_state.cart:
        total = sum(p for _, p in st.session_state.cart)
        for item, price in st.session_state.cart: st.write(f"- {item}: {price:,} تومان")
        st.write(f"**جمع: {total:,} تومان**")
        if st.button("ثبت سفارش (آزمایشی)"):
            st.balloons()
            st.success("سفارش ثبت شد (شبیه‌سازی)")
            st.session_state.cart = []

# ========== مهندس IT ==========
elif menu == "👨‍💻 مهندس IT":
    st.subheader("👨‍💻 مهندس IT")
    issues = {"وای‌فای قطع شده": "WiFi keeps disconnecting on Windows 11", "کندی ویندوز": "Windows 10 running very slow, how to speed up", "نصب پایتون": "How to install Python on Windows 11", "رفع ارور 404": "What does HTTP 404 error mean and how to fix", "مشکل پرینتر": "Printer not responding, troubleshooting steps"}
    c1, c2 = st.columns([1,2])
    with c1: selected = st.selectbox("مشکلات رایج:", ["(انتخاب کنید)"] + list(issues.keys()))
    with c2: free_q = st.text_input("یا سوالت رو مستقیم بنویس:")
    if st.button("کمک بگیر"):
        if selected != "(انتخاب کنید)": q = issues[selected]
        elif free_q: q = free_q
        else: st.warning("لطفاً سوال وارد کن."); st.stop()
        if any('\u0600' <= c <= '\u06FF' for c in q): q = tr.translate(q, dest='en').text
        prompt = "You are a skilled and friendly IT engineer. Give a helpful answer: " + q
        res = query_hf("microsoft/DialoGPT-small", {"inputs": prompt})
        reply = res[0]['generated_text'].split(prompt)[-1].strip() if res and isinstance(res, list) and 'generated_text' in res[0] else "خطا"
        st.write(reply)
