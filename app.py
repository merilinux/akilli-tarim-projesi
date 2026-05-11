import streamlit as st
from google import genai
from PIL import Image
import pandas as pd
import random
import os
import json
import requests
import base64
from io import BytesIO
from datetime import datetime
import plotly.graph_objects as go

# ==========================================
# SAYFA AYARLARI VE ŞEFFAF/ESNEK TASARIM (CSS)
# ==========================================
st.set_page_config(page_title="Botanix — Akıllı Tarım", layout="wide", page_icon="🌿")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif;
        color: #4caf50;
        letter-spacing: -0.02em;
    }
    .stApp > header + div h1 {
        font-size: 2.6rem;
        background: linear-gradient(90deg, #4caf50, #81c784, #2e7d32);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .login-card, .metric-box, [data-testid="metric-container"] {
        background: rgba(76, 175, 80, 0.08) !important;
        border: 1px solid rgba(76, 175, 80, 0.2) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
    }
    .section-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #4caf50;
        margin-bottom: 12px;
        display: block;
    }
    .stTextInput > div > div > input,
    .stSelectbox > div > div {
        background: rgba(128, 128, 128, 0.05) !important;
        border: 1px solid rgba(76, 175, 80, 0.3) !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FIREBASE AYARLARI
# ==========================================
FIREBASE_HOST = "botanix-iot-default-rtdb.europe-west1.firebasedatabase.app"
FIREBASE_URL  = f"https://{FIREBASE_HOST}/botanix_sensor.json"

FIREBASE_DROUGHT_META_URL   = f"https://{FIREBASE_HOST}/botanix_drought_map/meta.json"
FIREBASE_DROUGHT_POINTS_URL = f"https://{FIREBASE_HOST}/botanix_drought_map/humidity_points.json"
FIREBASE_DROUGHT_IMG_URL    = f"https://{FIREBASE_HOST}/botanix_drought_map/map_image_b64.json"


def get_sensor_data_from_firebase():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    "soil": data.get("toprak_nemi", 0),
                    "temp": data.get("ortam_sicakligi", 25),
                    "hum":  data.get("hava_nemi", 55)
                }
            else:
                st.warning("⚠️ Firebase'de veri bulunamadı.")
        else:
            st.error(f"⚠️ Firebase Bağlantı Hatası: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Sunucuya erişilemiyor: {e}")
    return None


def get_drought_meta():
    try:
        r = requests.get(FIREBASE_DROUGHT_META_URL, timeout=5)
        if r.status_code == 200 and r.json():
            return r.json()
    except Exception:
        pass
    return None


def get_drought_points():
    try:
        r = requests.get(FIREBASE_DROUGHT_POINTS_URL, timeout=8)
        if r.status_code == 200 and r.json():
            return r.json()
    except Exception:
        pass
    return None


def get_drought_map_image():
    try:
        r = requests.get(FIREBASE_DROUGHT_IMG_URL, timeout=20)
        if r.status_code == 200:
            b64 = r.json()
            if b64 and isinstance(b64, str):
                img_bytes = base64.b64decode(b64)
                return Image.open(BytesIO(img_bytes))
    except Exception:
        pass
    return None


# ==========================================
# 1. KALICI VERİTABANI YÖNETİMİ (CSV)
# ==========================================
CSV_FILE = "tarim_veritabani.csv"

if not os.path.exists(CSV_FILE):
    df_empty = pd.DataFrame(columns=[
        "Kullanıcı ID", "Kullanıcı Adı", "Bahçe/Sera", "Tarih",
        "Ortam Sıcaklığı (°C)", "Hava Nemi (%)", "Toprak Nemi (%)"
    ])
    df_empty.to_csv(CSV_FILE, index=False)


def load_database():
    return pd.read_csv(CSV_FILE)


def save_to_database(new_row_df):
    new_row_df.to_csv(CSV_FILE, mode='a', header=False, index=False)


# ==========================================
# 2. KALICI VE "AKILLI" PROFİL YÖNETİMİ (JSON)
# ==========================================
USERS_FILE = "kullanicilar.json"

DEFAULT_USERS = {
    "TR-1000": {"ad": "Meryem Derin",  "telefon": "5550000000", "bahceler": ["Konya Merkez Lale Serası", "Çumra Domates Tesisleri"]},
    "TR-1001": {"ad": "Melih Geylani", "telefon": "5550000001", "bahceler": ["Ereğli Organik Çilek"]},
    "TR-1002": {"ad": "Juri1",         "telefon": "000",         "bahceler": ["Genel Test Serası"]}
}


def load_and_sync_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_USERS, f, ensure_ascii=False, indent=4)
        return DEFAULT_USERS
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        kayitli = json.load(f)
    guncellendi = False
    for uid, data in DEFAULT_USERS.items():
        if uid not in kayitli:
            kayitli[uid] = data
            guncellendi = True
    if guncellendi:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(kayitli, f, ensure_ascii=False, indent=4)
    return kayitli


def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=4)


GUNCEL_KULLANICILAR = load_and_sync_users()

# ==========================================
# OTURUM (SESSION) YÖNETİMİ
# ==========================================
for key, default in [
    ("logged_in", False), ("user_id", ""), ("user_name", ""),
    ("aktif_bahce", ""), ("kullanici_bahceleri", []),
    ("is_guest", False), ("sensor_data", {"temp": 0, "hum": 0, "soil": 0})
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ==========================================
# EKRAN 1: GİRİŞ EKRANI
# ==========================================
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center; padding: 20px; margin-bottom: 20px;">
        <h1 style="font-size: 3rem;">🌿 Botanix</h1>
        <p style="font-size: 1.1rem; opacity: 0.8;">Otonom Tarım Yönetim Platformu</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<span class="section-label">🧑‍🌾 Kayıtlı Çiftçi Girişi</span>', unsafe_allow_html=True)
        girilen_id = st.text_input("Müşteri ID", placeholder="Örn: TR-1000", key="login_id", label_visibility="collapsed").strip().upper()
        if st.button("→ Sisteme Giriş Yap", use_container_width=True):
            if girilen_id in GUNCEL_KULLANICILAR:
                st.session_state.logged_in          = True
                st.session_state.is_guest           = False
                st.session_state.user_id            = girilen_id
                st.session_state.user_name          = GUNCEL_KULLANICILAR[girilen_id]["ad"]
                st.session_state.kullanici_bahceleri = GUNCEL_KULLANICILAR[girilen_id]["bahceler"]
                st.session_state.aktif_bahce        = st.session_state.kullanici_bahceleri[0]
                st.rerun()
            else:
                st.error("❌ Kayıtlı kullanıcı bulunamadı.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<span class="section-label">🔍 Misafir / Ziyaretçi Girişi</span>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.85rem; opacity:0.75; margin-bottom:16px;">Jüri üyeleri ve test amaçlı ziyaretler için.</p>', unsafe_allow_html=True)
        if st.button("→ Misafir Olarak Devam Et", use_container_width=True):
            st.session_state.logged_in          = True
            st.session_state.is_guest           = True
            st.session_state.user_id            = f"GUEST-{random.randint(1000, 9999)}"
            st.session_state.user_name          = "Misafir Ziyaretçi"
            st.session_state.kullanici_bahceleri = ["Misafir Test Serası"]
            st.session_state.aktif_bahce        = "Misafir Test Serası"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📝 Sistemi Kullanmaya Başlayın: Yeni Çiftçi Kaydı Oluştur", expanded=False):
        st.markdown('<span class="section-label">Ücretsiz Ön Kayıt</span>', unsafe_allow_html=True)
        yeni_ad    = st.text_input("Ad - Soyad",          placeholder="Örn: Meryem Derin")
        yeni_tel   = st.text_input("Telefon Numarası",    placeholder="Örn: 0555 123 4567")
        yeni_bahce = st.text_input("İlk Saha/Sera Adı",   placeholder="Örn: Konya Merkez Lale Serası")
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_buton, _ = st.columns([1, 2, 1])
        with col_buton:
            kayit_tiklandi = st.button("Sisteme Kayıt Ol", use_container_width=True)
        if kayit_tiklandi:
            if yeni_ad and yeni_tel and yeni_bahce:
                temiz_tel = yeni_tel.replace(" ", "")
                kayitli_id = next(
                    (uid for uid, v in GUNCEL_KULLANICILAR.items()
                     if v.get("telefon", "").replace(" ", "") == temiz_tel), None
                )
                if kayitli_id:
                    st.error(f"🚨 Bu telefon zaten kayıtlı! ID: **{kayitli_id}**")
                else:
                    while True:
                        yeni_id = f"TR-{random.randint(2000, 9999)}"
                        if yeni_id not in GUNCEL_KULLANICILAR:
                            break
                    GUNCEL_KULLANICILAR[yeni_id] = {"ad": yeni_ad, "telefon": temiz_tel, "bahceler": [yeni_bahce]}
                    save_users(GUNCEL_KULLANICILAR)
                    st.success(f"🎉 Kayıt Başarılı! ID'niz: **{yeni_id}**")
                    st.info("Bu ID'yi not alın ve yukarıdan giriş yapın.")
            else:
                st.warning("Lütfen tüm alanları doldurunuz.")

# ==========================================
# EKRAN 2: ANA UYGULAMA
# ==========================================
else:
    with st.sidebar:
        st.markdown(f"""
        <div class="login-card" style="margin-bottom:16px;">
            <div class="section-label" style="font-size:0.7rem; margin-bottom:6px;">Aktif Oturum</div>
            <div style="font-size:1.05rem;font-weight:600;margin-bottom:2px;">{st.session_state.user_name}</div>
            <div style="font-size:0.78rem;opacity:0.7;">{st.session_state.user_id}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<span class="section-label">🏡 Saha / Sera Seçimi</span>', unsafe_allow_html=True)
        secilen = st.selectbox(
            "Aktif Saha",
            options=st.session_state.kullanici_bahceleri,
            index=st.session_state.kullanici_bahceleri.index(st.session_state.aktif_bahce)
                  if st.session_state.aktif_bahce in st.session_state.kullanici_bahceleri else 0,
            label_visibility="collapsed"
        )
        if secilen != st.session_state.aktif_bahce:
            st.session_state.aktif_bahce = secilen
            st.rerun()

        if not st.session_state.is_guest:
            with st.expander("➕ Yeni Saha Ekle"):
                yeni_bahce_adi = st.text_input("Bölge Adı", placeholder="Örn: Yonca Tarlası")
                if st.button("Ekle", use_container_width=True):
                    if yeni_bahce_adi and yeni_bahce_adi not in st.session_state.kullanici_bahceleri:
                        st.session_state.kullanici_bahceleri.append(yeni_bahce_adi)
                        st.session_state.aktif_bahce = yeni_bahce_adi
                        GUNCEL_KULLANICILAR[st.session_state.user_id]["bahceler"].append(yeni_bahce_adi)
                        save_users(GUNCEL_KULLANICILAR)
                        st.success(f"✅ {yeni_bahce_adi} eklendi.")
                        st.rerun()
                    elif yeni_bahce_adi in st.session_state.kullanici_bahceleri:
                        st.warning("Bu bölge zaten kayıtlı.")

        st.divider()
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.aktif_bahce = ""
            st.session_state.kullanici_bahceleri = []
            st.rerun()

        st.divider()
        st.markdown('<span class="section-label">⚙️ Sistem</span>', unsafe_allow_html=True)
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("🔑 API Aktif")
        except Exception:
            api_key = None
            st.error("⚠️ API Anahtarı Eksik")

    st.markdown(f"""
    <div style="margin-bottom:8px;">
        <h1 style="margin-bottom:4px;">🌿 Botanix</h1>
        <div style="font-size:0.85rem;opacity:0.75;letter-spacing:0.04em;">
            Otonom Tarım Yönetim Platformu &nbsp;·&nbsp; {st.session_state.aktif_bahce}
        </div>
    </div>
    """, unsafe_allow_html=True)

    genel_veritabani = load_database()

    if st.session_state.is_guest:
        kullanici_verisi = pd.DataFrame(columns=genel_veritabani.columns)
    else:
        kullanici_verisi = genel_veritabani[
            (genel_veritabani["Kullanıcı ID"] == st.session_state.user_id) &
            (genel_veritabani["Bahçe/Sera"]   == st.session_state.aktif_bahce)
        ]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📸  Anlık Analiz",
        "📅  Gelişim Ajandası",
        "🔮  Proaktif Risk Tahmini",
        "🚁  Otonom Uçuş (Faz-2)",
        "🗺️  Kuraklık Haritası"
    ])

    # ==========================================
    # TAB 1 — ANLIK ANALİZ
    # ==========================================
    with tab1:
        st.markdown(f'<span class="section-label">📡 IoT Sensör Ağı — {st.session_state.aktif_bahce}</span>', unsafe_allow_html=True)

        if st.button("📡 ESP32 Sensör Verilerini Çek", use_container_width=False):
            with st.spinner("Bulut üzerinden ESP32 ile haberleşiliyor..."):
                gercek_veri = get_sensor_data_from_firebase()
                if gercek_veri:
                    st.session_state.sensor_data = gercek_veri
                    st.success("✅ Güncel veriler alındı.")
                else:
                    st.error("ESP32 verisi alınamadı.")

        met_col1, met_col2, met_col3 = st.columns(3)
        met_col1.metric("🌡 Ortam Sıcaklığı", f"{st.session_state.sensor_data['temp']} °C")
        met_col2.metric("💧 Hava Nemi",        f"%{st.session_state.sensor_data['hum']}")
        met_col3.metric("🌱 Toprak Nemi",      f"%{st.session_state.sensor_data['soil']}")

        st.divider()
        st.markdown('<span class="section-label">📷 Görüntü Girişi</span>', unsafe_allow_html=True)
        image = None

        with st.expander("Görsel Kaynağı Seçin", expanded=False):
            gorsel_secimi = st.radio("Kaynak:", ["📸 Canlı Kamera", "📁 Dosyadan Yükle"], horizontal=True, label_visibility="collapsed")
            if gorsel_secimi == "📸 Canlı Kamera":
                kamera_fotosu = st.camera_input("Fotoğraf Çek", label_visibility="collapsed")
                if kamera_fotosu:
                    image = Image.open(kamera_fotosu)
                    st.success("✅ Görüntü yakalandı.")
            elif gorsel_secimi == "📁 Dosyadan Yükle":
                uploaded_file = st.file_uploader("Fotoğraf Yükle", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.success("✅ Görüntü aktarıldı.")
                    st.image(image, caption=f"{st.session_state.aktif_bahce} — Analiz Görüntüsü", width="stretch")

        st.divider()
        st.markdown('<span class="section-label">🤖 Multimodal Yapay Zekâ Analizi</span>', unsafe_allow_html=True)

        if st.button(f"⚡ {st.session_state.aktif_bahce} Verilerini Sentezle", use_container_width=True):
            if not api_key:
                st.error("⚠️ API Anahtarı eksik!")
            elif not image:
                st.warning("⚠️ Lütfen önce bir görüntü sağlayın.")
            else:
                with st.spinner("Multimodal analiz yürütülüyor..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        past_data_str = kullanici_verisi.to_string(index=False) if not kullanici_verisi.empty else "Henüz geçmiş veri yok."
                        c_temp = st.session_state.sensor_data['temp']
                        c_hum  = st.session_state.sensor_data['hum']
                        c_soil = st.session_state.sensor_data['soil']

                        prompt = f"""
                        Sen otonom kararlar alabilen bir "Multimodal Tarım Yapay Zekası"sın.
                        Kullanıcı: {st.session_state.user_name}
                        İncelenen Bölge: {st.session_state.aktif_bahce}

                        GÖREV 1: SAHTELİK KONTROLÜ
                        Fotoğraftaki bitki SUNİ/YAPAY/PLASTİK ise "[SAHTE]" yaz. Gerçek ise "[GERÇEK]" yaz ve analize geç:

                        [ANLIK IoT VERİLERİ]
                        - Ortam Sıcaklığı: {c_temp} °C
                        - Hava Nemi: %{c_hum}
                        - Toprak Nemi: %{c_soil}

                        [VERİ TABANI GEÇMİŞİ]
                        {past_data_str}

                        Kullanıcıya ({st.session_state.user_name}) hitap ederek profesyonel bir SaaS raporu oluştur:
                        ### 🌿 Bitki Taksonomisi ve Görsel Stres Analizi
                        ### 📊 Sensör Füzyonu (Görsel ve Çevresel Veri Uyumu)
                        ### 📉 Su İhtiyacı ve Gelişim Trendi
                        ### 💧 Otonom Sulama Valfi Tetikleme Kararı
                        """

                        response      = client.models.generate_content(model='gemini-2.5-flash-lite', contents=[prompt, image])
                        response_text = response.text

                        if "[SAHTE]" in response_text:
                            st.error("🚨 UYARI: Görüntüdeki bitki SUNİ/PLASTİK olarak tespit edildi! Kayıt engellendi.")
                        elif "[GERÇEK]" in response_text:
                            st.success(f"✅ Analiz tamamlandı — {st.session_state.aktif_bahce}")
                            st.markdown(response_text.replace("[GERÇEK]", "").strip())
                            if not st.session_state.is_guest:
                                new_data = pd.DataFrame({
                                    "Kullanıcı ID":        [st.session_state.user_id],
                                    "Kullanıcı Adı":       [st.session_state.user_name],
                                    "Bahçe/Sera":          [st.session_state.aktif_bahce],
                                    "Tarih":               [datetime.now().strftime("%Y-%m-%d %H:%M")],
                                    "Ortam Sıcaklığı (°C)":[c_temp],
                                    "Hava Nemi (%)":       [c_hum],
                                    "Toprak Nemi (%)":     [c_soil]
                                })
                                save_to_database(new_data)
                                st.info("💾 Analiz sonucu veritabanına kalıcı olarak kaydedildi.")
                            else:
                                st.warning("⚠️ Misafir oturumunda kayıt tutulmamaktadır.")
                        else:
                            st.markdown(response_text)
                    except Exception as e:
                        st.error(f"Sistem Hatası: {e}")

    # ==========================================
    # TAB 2 — GELİŞİM AJANDASI
    # ==========================================
    with tab2:
        st.markdown(f'<span class="section-label">📅 Kalıcı Veri Tabanı — {st.session_state.aktif_bahce}</span>', unsafe_allow_html=True)

        if st.session_state.is_guest:
            st.warning("Misafir oturumlarında kayıt tutulmaz. Geçmişe erişmek için Çiftçi ID'niz ile giriş yapın.")
        else:
            guncel_veritabani   = load_database()
            kullanici_guncel_veri = guncel_veritabani[
                (guncel_veritabani["Kullanıcı ID"] == st.session_state.user_id) &
                (guncel_veritabani["Bahçe/Sera"]   == st.session_state.aktif_bahce)
            ]
            st.markdown(f'<p style="font-size:0.88rem;opacity:0.8;">**{st.session_state.aktif_bahce}** bölgesi için kaydedilen sensör okumalarının zaman serisi.</p>', unsafe_allow_html=True)
            if not kullanici_guncel_veri.empty:
                st.dataframe(kullanici_guncel_veri, use_container_width=True)
                st.divider()
                st.markdown('<span class="section-label">📉 Zaman Serisi Analizi</span>', unsafe_allow_html=True)
                chart_data = kullanici_guncel_veri.set_index("Tarih")[["Ortam Sıcaklığı (°C)", "Hava Nemi (%)", "Toprak Nemi (%)"]]
                st.line_chart(chart_data)
            else:
                st.info(f"ℹ️ {st.session_state.aktif_bahce} için henüz kayıt yok. İlk analizi 'Anlık Analiz' sekmesinden başlatın.")

    # ==========================================
    # TAB 3 — PROAKTİF RİSK TAHMİNİ
    # ==========================================
    with tab3:
        st.markdown(f'<span class="section-label">🔮 Proaktif Karar Destek — {st.session_state.aktif_bahce}</span>', unsafe_allow_html=True)
        col3, col4 = st.columns(2, gap="large")
        with col3:
            sim_temp = st.slider("Tahmini Sıcaklık (°C)",  10.0, 50.0, 32.0, step=0.5, key="sim_temp")
            sim_hum  = st.slider("Tahmini Hava Nemi (%)",   0.0,100.0, 85.0, step=1.0, key="sim_hum")
        with col4:
            sim_soil = st.slider("Tahmini Toprak Nemi (%)", 0.0,100.0, 15.0, step=1.0, key="sim_soil")
            sim_days = st.selectbox("Tahmin Ufku (Gün)", [1,3,4,5,6,7,8,9,10,11,12,13,14], key="sim_days")

        if st.button(f"⏳ {sim_days} Günlük Senaryoyu Simüle Et", use_container_width=True):
            if not api_key:
                st.error("⚠️ API Anahtarı eksik!")
            else:
                with st.spinner("Senaryo hesaplanıyor..."):
                    try:
                        client     = genai.Client(api_key=api_key)
                        guncel_db  = load_database()
                        guncel_gecmis = guncel_db[
                            (guncel_db["Kullanıcı ID"] == st.session_state.user_id) &
                            (guncel_db["Bahçe/Sera"]   == st.session_state.aktif_bahce)
                        ]
                        past_data_str = guncel_gecmis.to_string(index=False) if not guncel_gecmis.empty else "Geçmiş veri yok."

                        sim_prompt = f"""
                        Sen bitki hastalıklarını ve su stresini önceden tahmin eden proaktif bir Karar Destek Sistemisin.
                        Müşteri: {st.session_state.user_name}
                        İncelenen Saha: {st.session_state.aktif_bahce}
                        Geçmiş Veriler: {past_data_str}

                        Gelecek ({sim_days} gün sonraki) senaryo:
                        - Sıcaklık: {sim_temp} °C
                        - Hava Nemi: %{sim_hum}
                        - Toprak Nemi: %{sim_soil}

                        Eğer risk varsa cevabının EN BAŞINA [HASTALIK_ALARM: Riskin Adı] etiketini koy.
                        Detaylı raporunu sun:
                        ### ⚠️ Tespit Edilen Risk Seviyesi
                        ### 🔬 Hastalığın/Stresin Oluşma Mekanizması
                        ### 🛡️ Proaktif Müdahale
                        """
                        sim_response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=sim_prompt)
                        sim_text     = sim_response.text

                        if "[HASTALIK_ALARM:" in sim_text:
                            start_idx   = sim_text.find("[HASTALIK_ALARM:") + 16
                            end_idx     = sim_text.find("]", start_idx)
                            hastalik_adi = sim_text[start_idx:end_idx].strip()
                            st.markdown(f'<div style="background:rgba(244,67,54,0.1);border-left:4px solid #f44336;padding:15px;border-radius:8px;margin-bottom:20px;">🚨 KRİTİK ERKEN UYARI — {hastalik_adi} tehlikesi tespit edildi!</div>', unsafe_allow_html=True)
                            st.markdown(sim_text[end_idx+1:].strip())
                        else:
                            st.success("✅ Risk tespit edilmedi.")
                            st.markdown(sim_text)
                    except Exception as e:
                        st.error(f"Hata: {e}")

    # ==========================================
    # TAB 4 — DRONE UÇUŞ PLANLAYICI
    # ==========================================
    with tab4:
        st.markdown('<span class="section-label">🚁 Otonom Drone Uçuş Planlayıcı (Uydu Haritası)</span>', unsafe_allow_html=True)
        st.markdown("""
        <p style='font-size:0.9rem; opacity:0.8;'>
        Algoritma, otonom uçuş sırasında kameranın (mavi kutunun) tarlanın dışına taşmasını engellemek için
        drone'un rotasını (sarı çizgi) güvenli bir iç çembere hapseder.
        Kamera ayak izi, tarlanın sınırlarına milimetrik olarak teğet geçer.
        </p>
        """, unsafe_allow_html=True)

        SENIN_GITHUB_RESIM_LINKIN = "https://raw.githubusercontent.com/merilinux/akilli-tarim-projesi/main/Gemini_Generated_Image_uvl9gtuvl9gtuvl9.png"
        GITHUB_GELISTIRME_MODE    = True

        with st.expander("📍 Tarla Sınırlarını Belirle (Poligon Koordinatları)", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                x1 = st.number_input("Sol Alt X", value=320)
                y1 = st.number_input("Sol Alt Y", value=170)
            with c2:
                x2 = st.number_input("Sağ Alt X", value=800)
                y2 = st.number_input("Sağ Alt Y", value=170)
            with c3:
                x3 = st.number_input("Sağ Üst X", value=800)
                y3 = st.number_input("Sağ Üst Y", value=355)
            with c4:
                x4 = st.number_input("Sol Üst X", value=320)
                y4 = st.number_input("Sol Üst Y", value=355)

        poligon = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]

        col_slider1, col_slider2 = st.columns(2)
        with col_slider1:
            irtifa  = st.slider("Uçuş İrtifası (m)",  min_value=30, max_value=120, value=50,  step=5)
        with col_slider2:
            binisme = st.slider("Binişme Oranı (%)",  min_value=50, max_value=90,  value=70,  step=5)

        tarla_genisligi   = 1000
        tarla_uzunlugu    = 500
        kamera_gorus_acisi = 1.5
        kapsama = irtifa * kamera_gorus_acisi
        adim    = max(kapsama * (1 - binisme / 100.0), 5)

        tarla_min_x = min(p[0] for p in poligon)
        tarla_max_x = max(p[0] for p in poligon)
        tarla_min_y = min(p[1] for p in poligon)
        tarla_max_y = max(p[1] for p in poligon)

        guvenli_min_x = tarla_min_x + kapsama / 2
        guvenli_max_x = tarla_max_x - kapsama / 2
        guvenli_min_y = tarla_min_y + kapsama / 2
        guvenli_max_y = tarla_max_y - kapsama / 2

        wp_x, wp_y = [], []

        if guvenli_min_x <= guvenli_max_x and guvenli_min_y <= guvenli_max_y:
            mevcut_y = guvenli_min_y
            yon = 1
            while mevcut_y <= guvenli_max_y + 0.1:
                satir_x = []
                mx = guvenli_min_x
                while mx <= guvenli_max_x + 0.1:
                    satir_x.append(mx)
                    mx += adim
                if abs(satir_x[-1] - guvenli_max_x) > 1.0:
                    satir_x.append(guvenli_max_x)
                if yon == -1:
                    satir_x.reverse()
                for nx in satir_x:
                    wp_x.append(nx)
                    wp_y.append(mevcut_y)
                mevcut_y += adim
                yon *= -1
        else:
            st.error("⚠️ İrtifa çok yüksek! Lütfen irtifayı düşürün.")

        toplam_waypoint = len(wp_x)
        toplam_mesafe   = sum(((wp_x[i]-wp_x[i-1])**2 + (wp_y[i]-wp_y[i-1])**2)**0.5 for i in range(1, len(wp_x))) if wp_x else 0
        tahmini_sure    = (toplam_mesafe / 5) / 60 if toplam_waypoint > 0 else 0

        fig = go.Figure()

        if GITHUB_GELISTIRME_MODE:
            fig.add_layout_image(dict(
                source=SENIN_GITHUB_RESIM_LINKIN,
                xref="x", yref="y", x=0, y=tarla_uzunlugu,
                sizex=tarla_genisligi, sizey=tarla_uzunlugu,
                sizing="stretch", opacity=0.9, layer="below"
            ))

        poligon_x = [tarla_min_x, tarla_max_x, tarla_max_x, tarla_min_x, tarla_min_x]
        poligon_y = [tarla_min_y, tarla_min_y, tarla_max_y, tarla_max_y, tarla_min_y]
        fig.add_trace(go.Scatter(
            x=poligon_x, y=poligon_y, mode='lines',
            fill='toself', fillcolor='rgba(0,229,255,0.1)',
            line=dict(color='cyan', width=2, dash="dash"),
            name="Seçilen Tarla Alanı", hoverinfo='skip'
        ))

        if wp_x and wp_y:
            fig.add_trace(go.Scatter(x=wp_x, y=wp_y, mode='lines', line=dict(color='yellow', width=2), hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=wp_x, y=wp_y, mode='markers', marker=dict(color='cyan', size=5), hoverinfo='skip'))

            def b_x(cx, w): return [cx-w/2, cx+w/2, cx+w/2, cx-w/2, cx-w/2]
            def b_y(cy, w): return [cy-w/2, cy-w/2, cy+w/2, cy+w/2, cy-w/2]

            fig.add_trace(go.Scatter(
                x=b_x(wp_x[0], kapsama), y=b_y(wp_y[0], kapsama),
                fill='toself', fillcolor='rgba(0,229,255,0.3)',
                line=dict(color='cyan', width=2, dash='dot'), hoverinfo='skip'
            ))
            fig.add_trace(go.Scatter(x=[wp_x[0]], y=[wp_y[0]], mode='text', text=['🚁'], textfont=dict(size=35), hoverinfo='skip'))

            frames = [go.Frame(data=[
                go.Scatter(x=b_x(wp_x[i], kapsama), y=b_y(wp_y[i], kapsama)),
                go.Scatter(x=[wp_x[i]], y=[wp_y[i]])
            ], traces=[3, 4]) for i in range(len(wp_x))]
            fig.frames = frames

            fig.update_layout(updatemenus=[dict(
                type="buttons", showactive=False, x=0.5, y=1.15,
                xanchor="center", yanchor="bottom", direction="left",
                buttons=[
                    dict(label="▶️ Otonom Uçuşu Başlat", method="animate",
                         args=[None, dict(frame=dict(duration=300, redraw=False),
                                          transition=dict(duration=300, easing="linear"),
                                          fromcurrent=True, mode="immediate")]),
                    dict(label="⏸️ Durdur", method="animate",
                         args=[[None], dict(frame=dict(duration=0, redraw=False),
                                            mode="immediate", transition=dict(duration=0))])
                ]
            )])

        padding = kapsama * 0.8
        fig.update_layout(
            xaxis=dict(range=[tarla_min_x-padding, tarla_max_x+padding], showgrid=False, zeroline=False, visible=False),
            yaxis=dict(range=[tarla_min_y-padding, tarla_max_y+padding], scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, visible=False),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=20, b=0), height=550, showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        met1, met2, met3 = st.columns(3)
        met1.metric("📌 Toplam Waypoint",      f"{toplam_waypoint} Adet")
        met2.metric("📏 Toplam Rota Uzunluğu", f"{int(toplam_mesafe)} Metre")
        met3.metric("⏱️ Tahmini Uçuş Süresi",  f"{tahmini_sure:.1f} Dakika")

    # ==========================================
    # TAB 5 — KURAKLAK HARİTASI
    # ==========================================
    with tab5:
        st.markdown('<span class="section-label">🗺️ Otonom Drone Kuraklık Haritası — Canlı Firebase</span>', unsafe_allow_html=True)

        # Görev durumu banner
        meta = get_drought_meta()

        if meta:
            status       = meta.get("mission_status", "BİLİNMİYOR")
            status_icon  = "✅" if status == "TAMAMLANDI" else "🚁"
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("📡 Görev Durumu",    f"{status_icon} {status}")
            col_m2.metric("📌 Ölçüm Noktası",   f"{meta.get('total_points', 0)} Adet")
            col_m3.metric("💧 Ort. Toprak Nemi", f"%{meta.get('avg_toprak_nemi', 0):.1f}")
            col_m4.metric("🌡 Ort. Sıcaklık",   f"{meta.get('avg_sicaklik', 0):.1f} °C")
            st.caption(f"Son güncelleme: {meta.get('last_updated', 'Bilinmiyor')}")
        else:
            st.info("ℹ️ Drone henüz uçmadı veya Firebase bağlantısı yok. Drone görevini başlatın.")

        st.divider()

        col_btn1, col_btn2, _ = st.columns([1, 1, 3])
        with col_btn1:
            st.button("🔄 Haritayı Yenile", use_container_width=True)
        with col_btn2:
            goster_png = st.toggle("📷 OpenCV PNG Görünümü", value=False)

        st.divider()

        # Plotly interaktif harita
        st.markdown('<span class="section-label">📊 İnteraktif Nem Dağılımı (Plotly)</span>', unsafe_allow_html=True)

        pts_data = get_drought_points()

        if pts_data and len(pts_data) >= 2:
            xs   = [p["x"]           for p in pts_data]
            ys   = [p["y"]           for p in pts_data]
            nems = [p["toprak_nemi"] for p in pts_data]
            hava = [p["hava_nemi"]   for p in pts_data]
            sics = [p["sicaklik"]    for p in pts_data]

            fig_d = go.Figure()

            # Drone izi
            fig_d.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines",
                line=dict(color="rgba(255,255,255,0.2)", width=1),
                hoverinfo="skip", name="Drone Yolu"
            ))

            # Nem noktaları — renk skalası
            fig_d.add_trace(go.Scatter(
                x=xs, y=ys, mode="markers",
                marker=dict(
                    size=14,
                    color=nems,
                    colorscale=[
                        [0.0, "#d32f2f"],
                        [0.3, "#ff7043"],
                        [0.5, "#ffb300"],
                        [0.7, "#66bb6a"],
                        [1.0, "#1565c0"],
                    ],
                    cmin=0, cmax=100,
                    colorbar=dict(
                        title="Toprak Nemi (%)",
                        tickvals=[0, 25, 40, 50, 70, 100],
                        ticktext=["0% Kurak", "25%", "40% Eşik", "50%", "70%", "100% Nemli"],
                        thickness=16, len=0.8,
                    ),
                    showscale=True,
                    line=dict(color="white", width=1),
                ),
                customdata=list(zip(hava, sics)),
                hovertemplate=(
                    "<b>Konum:</b> (%{x:.1f}, %{y:.1f})<br>"
                    "<b>Toprak Nemi:</b> %{marker.color:.1f}%<br>"
                    "<b>Hava Nemi:</b> %{customdata[0]:.1f}%<br>"
                    "<b>Sıcaklık:</b> %{customdata[1]:.1f} °C<extra></extra>"
                ),
                name="Ölçüm Noktaları"
            ))

            # Kuraklık eşiği altındaki noktalar — kırmızı X
            kurak_pts = [p for p in pts_data if p["toprak_nemi"] < 40]
            if kurak_pts:
                fig_d.add_trace(go.Scatter(
                    x=[p["x"] for p in kurak_pts],
                    y=[p["y"] for p in kurak_pts],
                    mode="markers",
                    marker=dict(symbol="x", size=18, color="red", line=dict(width=3)),
                    name="⚠️ Kurak Bölge (<40%)",
                    hovertemplate="<b>KURAK BÖLGE</b><extra></extra>"
                ))

            fig_d.update_layout(
                plot_bgcolor="rgba(20,20,20,0.95)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)", color="#aaa", title="X Konumu (m)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.07)", color="#aaa", title="Y Konumu (m)", scaleanchor="x"),
                legend=dict(bgcolor="rgba(30,30,30,0.7)", bordercolor="rgba(76,175,80,0.3)", borderwidth=1, font=dict(color="#ddd")),
                height=520,
                margin=dict(l=20, r=20, t=20, b=20),
                hovermode="closest",
            )
            st.plotly_chart(fig_d, use_container_width=True)

            # Özet kutu
            kurak_sayisi = len(kurak_pts)
            kurak_oran   = (kurak_sayisi / len(pts_data)) * 100
            risk_renk    = "#f44336" if kurak_oran > 30 else "#ff9800" if kurak_oran > 10 else "#4caf50"
            risk_ikon    = "🔴" if kurak_oran > 30 else "🟡" if kurak_oran > 10 else "🟢"

            st.markdown(f"""
            <div style="background:rgba(76,175,80,0.08);border:1px solid rgba(76,175,80,0.2);
                        border-radius:12px;padding:16px;margin-top:12px;">
                <span class="section-label">📊 Saha Kuraklık Özeti</span>
                <p style="margin:0;font-size:0.95rem;">
                {risk_ikon} Tarlanın <strong style="color:{risk_renk}">%{kurak_oran:.1f}</strong>'i
                kuraklık eşiğinin altında (&lt;%40 toprak nemi) &nbsp;·&nbsp;
                {kurak_sayisi} / {len(pts_data)} ölçüm noktası kritik
                </p>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="background:rgba(255,152,0,0.08);border:1px solid rgba(255,152,0,0.25);
                        border-radius:12px;padding:24px;text-align:center;">
                <p style="font-size:1rem;opacity:0.8;margin:0;">
                📡 Firebase'de henüz harita verisi yok.<br>
                <span style="font-size:0.85rem;">Drone görevini başlatın; uçuş sırasında her 5 saniyede canlı güncellenir.</span>
                </p>
            </div>
            """, unsafe_allow_html=True)

        # OpenCV PNG görünümü
        if goster_png:
            st.divider()
            st.markdown('<span class="section-label">🖼️ Drone\'un Ürettiği Kuraklık Haritası (OpenCV)</span>', unsafe_allow_html=True)
            with st.spinner("Firebase'den harita PNG indiriliyor..."):
                map_img = get_drought_map_image()
            if map_img:
                st.image(map_img, caption="Drone görevinin ürettiği kuraklık haritası (IDW interpolasyon)", use_container_width=True)
                st.success("✅ Harita başarıyla yüklendi.")
            else:
                st.warning("⚠️ Henüz final harita yüklenmemiş. Drone görevi tamamlandığında burada görünecek.")
