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
# SAYFA AYARLARI — PREMIUM TASARIM
# ==========================================
st.set_page_config(page_title="Botanix — Akıllı Tarım", layout="wide", page_icon="🌿")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=Fraunces:ital,wght@0,300;0,600;0,700;1,300;1,600&display=swap');

    :root {
        --green-dim:   #1a2e1c;
        --green-mid:   #2d5a30;
        --green-main:  #3d8b40;
        --green-bright:#5cb85c;
        --green-glow:  #7dcf7d;
        --accent:      #a8e6cf;
        --gold:        #c8a96e;
        --surface-0:   #0d1a0e;
        --surface-1:   #111f12;
        --surface-2:   #162018;
        --surface-3:   #1c2a1e;
        --text-primary:#e8f5e2;
        --text-muted:  #7aaa7d;
        --border:      rgba(93,184,93,0.18);
        --border-hover:rgba(93,184,93,0.45);
        --glow:        0 0 30px rgba(61,139,64,0.15);
    }

    html, body, [class*="css"] {
        font-family: 'Sora', sans-serif;
        background-color: var(--surface-0) !important;
        color: var(--text-primary) !important;
    }

    /* ─── SCROLLBAR ─── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--surface-1); }
    ::-webkit-scrollbar-thumb { background: var(--green-mid); border-radius: 3px; }

    /* ─── APP BACKGROUND ─── */
    .stApp {
        background: radial-gradient(ellipse 80% 60% at 50% -10%, rgba(45,90,48,0.25) 0%, transparent 70%),
                    linear-gradient(180deg, var(--surface-0) 0%, #0a150b 100%) !important;
    }

    /* ─── HEADINGS ─── */
    h1, h2, h3, h4 {
        font-family: 'Fraunces', serif !important;
        color: var(--text-primary) !important;
    }

    /* ─── SECTION LABEL ─── */
    .section-label {
        font-family: 'Sora', sans-serif;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.18em;
        color: var(--green-glow);
        margin-bottom: 14px;
        display: block;
        padding-bottom: 6px;
        border-bottom: 1px solid var(--border);
    }

    /* ─── CARDS ─── */
    .login-card, .metric-box {
        background: linear-gradient(135deg, var(--surface-2), var(--surface-3)) !important;
        border: 1px solid var(--border) !important;
        border-radius: 20px !important;
        padding: 28px !important;
        box-shadow: var(--glow), inset 0 1px 0 rgba(255,255,255,0.04) !important;
        transition: border-color 0.3s, box-shadow 0.3s;
    }
    .login-card:hover {
        border-color: var(--border-hover) !important;
        box-shadow: 0 0 40px rgba(61,139,64,0.22), inset 0 1px 0 rgba(255,255,255,0.06) !important;
    }

    /* ─── METRIC CONTAINERS ─── */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, var(--surface-2), var(--surface-3)) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        padding: 18px 20px !important;
        box-shadow: var(--glow) !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--green-glow) !important;
        font-family: 'Fraunces', serif !important;
        font-size: 1.65rem !important;
    }

    /* ─── BUTTONS — PRIMARY ─── */
    .stButton > button {
        background: linear-gradient(135deg, var(--green-mid) 0%, var(--green-main) 100%) !important;
        color: #e8f5e2 !important;
        border: 1px solid rgba(93,184,93,0.35) !important;
        border-radius: 12px !important;
        font-family: 'Sora', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.06em !important;
        padding: 10px 20px !important;
        height: auto !important;
        min-height: 44px !important;
        transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        box-shadow: 0 2px 12px rgba(45,90,48,0.4), inset 0 1px 0 rgba(255,255,255,0.12) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--green-main) 0%, var(--green-bright) 100%) !important;
        border-color: rgba(93,184,93,0.7) !important;
        box-shadow: 0 4px 24px rgba(61,139,64,0.5), inset 0 1px 0 rgba(255,255,255,0.18) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: translateY(0px) scale(0.98) !important;
        box-shadow: 0 2px 8px rgba(45,90,48,0.4) !important;
    }

    /* ─── PRIMARY ACTION BUTTON (full-width / big CTA) ─── */
    .stButton > button[data-testid*="primary"], 
    div[data-testid="column"] .stButton > button {
        background: linear-gradient(135deg, #1e4d20 0%, var(--green-main) 60%, var(--green-bright) 100%) !important;
    }

    /* ─── INPUTS ─── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'Sora', sans-serif !important;
        transition: border-color 0.2s !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--green-main) !important;
        box-shadow: 0 0 0 3px rgba(61,139,64,0.15) !important;
    }

    /* ─── TABS ─── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface-1) !important;
        border-radius: 14px !important;
        padding: 4px !important;
        gap: 2px !important;
        border: 1px solid var(--border) !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-muted) !important;
        border-radius: 10px !important;
        font-family: 'Sora', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        padding: 8px 14px !important;
        transition: all 0.2s !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--green-mid), var(--green-main)) !important;
        color: #e8f5e2 !important;
        box-shadow: 0 2px 12px rgba(45,90,48,0.5) !important;
    }

    /* ─── SIDEBAR ─── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--surface-1) 0%, var(--surface-0) 100%) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--text-primary) !important; }

    /* ─── EXPANDER ─── */
    .streamlit-expanderHeader {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        font-family: 'Sora', sans-serif !important;
        font-size: 0.82rem !important;
        color: var(--text-primary) !important;
    }
    .streamlit-expanderContent {
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }

    /* ─── ALERTS ─── */
    .stSuccess { background: rgba(61,139,64,0.12) !important; border: 1px solid rgba(61,139,64,0.3) !important; border-radius: 10px !important; }
    .stWarning { background: rgba(200,169,110,0.12) !important; border: 1px solid rgba(200,169,110,0.3) !important; border-radius: 10px !important; }
    .stError   { background: rgba(244,67,54,0.12) !important; border: 1px solid rgba(244,67,54,0.3) !important; border-radius: 10px !important; }
    .stInfo    { background: rgba(61,139,64,0.08) !important; border: 1px solid rgba(61,139,64,0.2) !important; border-radius: 10px !important; }

    /* ─── DIVIDER ─── */
    hr { border-color: var(--border) !important; }

    /* ─── SPINNER ─── */
    .stSpinner > div { border-top-color: var(--green-bright) !important; }

    /* ─── DATAFRAME ─── */
    [data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden !important; }

    /* ─── SLIDER ─── */
    .stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] { 
        background: var(--green-main) !important; 
    }

    /* ─── TOGGLE ─── */
    .stToggle { accent-color: var(--green-bright); }

    /* ─── HERO BANNER ─── */
    .botanix-hero {
        background: linear-gradient(135deg, rgba(45,90,48,0.3) 0%, rgba(28,42,30,0.5) 100%);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 28px 36px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }
    .botanix-hero::before {
        content: '';
        position: absolute;
        top: -50%; right: -10%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(61,139,64,0.15) 0%, transparent 70%);
        pointer-events: none;
    }

    /* ─── STATUS BADGE ─── */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(61,139,64,0.15);
        border: 1px solid rgba(61,139,64,0.3);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        color: var(--green-glow);
        text-transform: uppercase;
    }
    .status-badge.flying {
        background: rgba(200,169,110,0.15);
        border-color: rgba(200,169,110,0.35);
        color: var(--gold);
        animation: pulse-gold 2s infinite;
    }
    @keyframes pulse-gold {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* ─── MAP TOGGLE BUTTON GROUP ─── */
    .map-btn-group {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
    }
    .map-btn-group .stButton > button {
        font-size: 0.75rem !important;
        padding: 8px 16px !important;
        min-height: 38px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FIREBASE AYARLARI
# ==========================================
FIREBASE_HOST = "botanix-iot-default-rtdb.europe-west1.firebasedatabase.app"
FIREBASE_URL  = f"https://{FIREBASE_HOST}/botanix_sensor.json"
FIREBASE_AUTH = "fVatRmIuJPhmJHUi7Ke9dRJvxKfw7qxbrw1TViz7"

FIREBASE_DROUGHT_META_URL   = f"https://{FIREBASE_HOST}/botanix_drought_map/meta.json?auth={FIREBASE_AUTH}"
FIREBASE_DROUGHT_POINTS_URL = f"https://{FIREBASE_HOST}/botanix_drought_map/humidity_points.json?auth={FIREBASE_AUTH}"
FIREBASE_DROUGHT_IMG_URL    = f"https://{FIREBASE_HOST}/botanix_drought_map/map_image_b64.json?auth={FIREBASE_AUTH}"


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
        import time as _tt
        url_nocache = FIREBASE_DROUGHT_IMG_URL + f"&t={int(_tt.time())}"
        r = requests.get(url_nocache, timeout=20)
        if r.status_code == 200:
            b64 = r.json()
            if b64 and isinstance(b64, str):
                img_bytes = base64.b64decode(b64)
                return Image.open(BytesIO(img_bytes))
    except Exception:
        pass
    return None


# ==========================================
# 1. VERİTABANI YÖNETİMİ (CSV)
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
# 2. PROFİL YÖNETİMİ (JSON)
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
# SESSION YÖNETİMİ
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
    <div style="text-align:center; padding: 60px 20px 40px; max-width:480px; margin:0 auto;">
        <div style="
            display:inline-block;
            background: linear-gradient(135deg, rgba(45,90,48,0.4), rgba(61,139,64,0.2));
            border: 1px solid rgba(93,184,93,0.25);
            border-radius: 24px;
            padding: 10px 22px;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.2em;
            color: #7dcf7d;
            text-transform: uppercase;
            margin-bottom: 20px;
        ">v2.0 — Faz II Aktif</div>
        <h1 style="
            font-family: 'Fraunces', serif;
            font-size: 3.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a8e6cf 0%, #5cb85c 50%, #3d8b40 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 10px;
            line-height: 1.1;
        ">🌿 Botanix</h1>
        <p style="font-size:1rem; color:#7aaa7d; font-weight:300; letter-spacing:0.04em; margin:0;">
            Otonom Tarım Yönetim Platformu
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        col1, col2 = st.columns(2, gap="medium")

        with col1:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">Çiftçi Girişi</span>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:0.8rem;color:#7aaa7d;margin-bottom:16px;">Müşteri ID\'niz ile oturum açın.</p>', unsafe_allow_html=True)
            girilen_id = st.text_input("Müşteri ID", placeholder="TR-1000", key="login_id", label_visibility="collapsed").strip().upper()
            if st.button("Sisteme Giriş →", use_container_width=True):
                if girilen_id in GUNCEL_KULLANICILAR:
                    st.session_state.logged_in          = True
                    st.session_state.is_guest           = False
                    st.session_state.user_id            = girilen_id
                    st.session_state.user_name          = GUNCEL_KULLANICILAR[girilen_id]["ad"]
                    st.session_state.kullanici_bahceleri = GUNCEL_KULLANICILAR[girilen_id]["bahceler"]
                    st.session_state.aktif_bahce        = st.session_state.kullanici_bahceleri[0]
                    st.rerun()
                else:
                    st.error("❌ Kullanıcı bulunamadı.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown('<span class="section-label">Misafir Erişimi</span>', unsafe_allow_html=True)
            st.markdown('<p style="font-size:0.8rem;color:#7aaa7d;margin-bottom:16px;">Jüri ve test amaçlı ziyaretler için.</p>', unsafe_allow_html=True)
            st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
            if st.button("Misafir Olarak Gir →", use_container_width=True):
                st.session_state.logged_in          = True
                st.session_state.is_guest           = True
                st.session_state.user_id            = f"GUEST-{random.randint(1000, 9999)}"
                st.session_state.user_name          = "Misafir Ziyaretçi"
                st.session_state.kullanici_bahceleri = ["Misafir Test Serası"]
                st.session_state.aktif_bahce        = "Misafir Test Serası"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("📝 Yeni Çiftçi Kaydı Oluştur", expanded=False):
            st.markdown('<span class="section-label">Ücretsiz Ön Kayıt</span>', unsafe_allow_html=True)
            yeni_ad    = st.text_input("Ad - Soyad",       placeholder="Meryem Derin")
            yeni_tel   = st.text_input("Telefon",          placeholder="0555 123 4567")
            yeni_bahce = st.text_input("İlk Saha Adı",     placeholder="Konya Merkez Lale Serası")
            st.markdown("<br>", unsafe_allow_html=True)
            _, col_buton, _ = st.columns([1, 2, 1])
            with col_buton:
                kayit_tiklandi = st.button("Kayıt Ol →", use_container_width=True)
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
                        st.info("Bu ID'yi not alın, yukarıdan giriş yapın.")
                else:
                    st.warning("Lütfen tüm alanları doldurunuz.")

# ==========================================
# EKRAN 2: ANA UYGULAMA
# ==========================================
else:
    # ─── SIDEBAR ─────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(45,90,48,0.3), rgba(28,42,30,0.5));
            border: 1px solid rgba(93,184,93,0.2);
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 18px;
        ">
            <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.15em;color:#7aaa7d;text-transform:uppercase;margin-bottom:6px;">Aktif Oturum</div>
            <div style="font-size:1.05rem;font-weight:600;color:#e8f5e2;margin-bottom:2px;">{st.session_state.user_name}</div>
            <div style="font-size:0.75rem;color:#5cb85c;font-family:'Sora',sans-serif;">{st.session_state.user_id}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<span class="section-label">Saha / Sera Seçimi</span>', unsafe_allow_html=True)
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
                yeni_bahce_adi = st.text_input("Bölge Adı", placeholder="Yonca Tarlası")
                if st.button("Ekle →", use_container_width=True):
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
        if st.button("🚪 Oturumu Kapat", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.aktif_bahce = ""
            st.session_state.kullanici_bahceleri = []
            st.rerun()

        st.divider()
        st.markdown('<span class="section-label">Sistem</span>', unsafe_allow_html=True)
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("🔑 Gemini API Aktif")
        except Exception:
            api_key = None
            st.error("⚠️ API Anahtarı Eksik")

    # ─── HERO BANNER ─────────────────────────
    st.markdown(f"""
    <div class="botanix-hero">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
            <div>
                <h1 style="font-family:'Fraunces',serif;font-size:2.1rem;margin:0 0 4px;
                    background:linear-gradient(135deg,#a8e6cf,#5cb85c);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
                    🌿 Botanix
                </h1>
                <div style="font-size:0.8rem;color:#7aaa7d;letter-spacing:0.04em;">
                    Otonom Tarım Yönetim Platformu &nbsp;·&nbsp; {st.session_state.aktif_bahce}
                </div>
            </div>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                <span class="status-badge">🟢 Sistem Online</span>
                <span class="status-badge" style="color:#c8a96e;background:rgba(200,169,110,0.12);border-color:rgba(200,169,110,0.3);">
                    Faz II — Drone Entegre
                </span>
            </div>
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
        "🔮  Risk Tahmini",
        "🚁  Otonom Uçuş",
        "🗺️  Kuraklık Haritası"
    ])

    # ==========================================
    # TAB 1 — ANLIK ANALİZ
    # ==========================================
    with tab1:
        st.markdown(f'<span class="section-label">📡 IoT Sensör Ağı — {st.session_state.aktif_bahce}</span>', unsafe_allow_html=True)

        col_btn, _ = st.columns([1, 3])
        with col_btn:
            if st.button("📡 Sensör Verisi Çek", use_container_width=True):
                with st.spinner("ESP32 ile haberleşiliyor..."):
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

        with st.expander("Görsel Kaynak Seç", expanded=False):
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
                    st.image(image, caption=f"{st.session_state.aktif_bahce} — Analiz Görüntüsü", use_container_width=True)

        st.divider()
        st.markdown('<span class="section-label">🤖 Multimodal AI Analizi</span>', unsafe_allow_html=True)

        if st.button(f"⚡ {st.session_state.aktif_bahce} — Verileri Sentezle", use_container_width=True):
            if not api_key:
                st.error("⚠️ API Anahtarı eksik!")
            elif not image:
                st.warning("⚠️ Önce bir görüntü sağlayın.")
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
                                st.info("💾 Analiz veritabanına kaydedildi.")
                            else:
                                st.warning("⚠️ Misafir oturumunda kayıt tutulmaz.")
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
            st.warning("Misafir oturumlarında kayıt tutulmaz.")
        else:
            guncel_veritabani   = load_database()
            kullanici_guncel_veri = guncel_veritabani[
                (guncel_veritabani["Kullanıcı ID"] == st.session_state.user_id) &
                (guncel_veritabani["Bahçe/Sera"]   == st.session_state.aktif_bahce)
            ]
            if not kullanici_guncel_veri.empty:
                st.dataframe(kullanici_guncel_veri, use_container_width=True)
                st.divider()
                st.markdown('<span class="section-label">📉 Zaman Serisi Analizi</span>', unsafe_allow_html=True)
                chart_data = kullanici_guncel_veri.set_index("Tarih")[["Ortam Sıcaklığı (°C)", "Hava Nemi (%)", "Toprak Nemi (%)"]]
                st.line_chart(chart_data)
            else:
                st.info(f"ℹ️ {st.session_state.aktif_bahce} için henüz kayıt yok.")

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
        st.markdown('<span class="section-label">🚁 Otonom Drone Uçuş Planlayıcı</span>', unsafe_allow_html=True)

        SENIN_GITHUB_RESIM_LINKIN = "https://raw.githubusercontent.com/merilinux/akilli-tarim-projesi/main/Gemini_Generated_Image_uvl9gtuvl9gtuvl9.png"
        GITHUB_GELISTIRME_MODE    = True

        with st.expander("📍 Tarla Sınırları (Poligon Koordinatları)", expanded=False):
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
            irtifa  = st.slider("Uçuş İrtifası (m)",  30, 120, 50, step=5)
        with col_slider2:
            binisme = st.slider("Binişme Oranı (%)",  50, 90,  70, step=5)

        tarla_genisligi    = 1000
        tarla_uzunlugu     = 500
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
            st.error("⚠️ İrtifa çok yüksek!")

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
            name="Tarla Alanı", hoverinfo='skip'
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
                    dict(label="▶ Otonom Uçuşu Başlat", method="animate",
                         args=[None, dict(frame=dict(duration=300, redraw=False),
                                          transition=dict(duration=300, easing="linear"),
                                          fromcurrent=True, mode="immediate")]),
                    dict(label="⏸ Durdur", method="animate",
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
        met2.metric("📏 Rota Uzunluğu",        f"{int(toplam_mesafe)} Metre")
        met3.metric("⏱️ Tahmini Uçuş Süresi",  f"{tahmini_sure:.1f} Dakika")

    # ==========================================
    # TAB 5 — KURAKLAK HARİTASI
    # ==========================================
    with tab5:
        if st.session_state.get("auto_refresh_map", False):
            import time as _t; _t.sleep(5)
            st.rerun()

        st.markdown('<span class="section-label">🗺️ Otonom Drone Kuraklık Haritası — Canlı Firebase</span>', unsafe_allow_html=True)

        meta = get_drought_meta()

        if meta:
            status       = meta.get("mission_status", "BİLİNMİYOR")
            is_flying    = status == "UCUYOR"
            status_icon  = "✅" if status == "TAMAMLANDI" else "🚁"
            badge_class  = "flying" if is_flying else ""
            st.markdown(f'<span class="status-badge {badge_class}">{status_icon} {status}</span>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("📡 Görev Durumu",    f"{status_icon} {status}")
            col_m2.metric("📌 Ölçüm Noktası",   f"{meta.get('total_points', 0)} Adet")
            col_m3.metric("💧 Ort. Toprak Nemi", f"%{meta.get('avg_toprak_nemi', 0):.1f}")
            col_m4.metric("🌡 Ort. Sıcaklık",   f"{meta.get('avg_sicaklik', 0):.1f} °C")
            st.caption(f"Son güncelleme: {meta.get('last_updated', 'Bilinmiyor')}")
        else:
            st.info("ℹ️ Drone henüz uçmadı veya Firebase bağlantısı yok.")

        st.divider()

        col_btn1, col_btn2, col_btn3, _ = st.columns([1.2, 1.2, 1.2, 2])
        with col_btn1:
            auto_ref = st.toggle("🔄 Otomatik Yenile (5sn)", value=st.session_state.get("auto_refresh_map", False))
            st.session_state["auto_refresh_map"] = auto_ref
        with col_btn2:
            goster_sicaklik = st.toggle("🌡 Sıcaklık Haritası", value=False)
        with col_btn3:
            goster_png = st.toggle("📷 OpenCV PNG", value=False)

        st.divider()

        pts_data = get_drought_points()

        if pts_data and len(pts_data) >= 2:
            xs   = [p["x"]           for p in pts_data]
            ys   = [p["y"]           for p in pts_data]
            nems = [p["toprak_nemi"] for p in pts_data]
            hava = [p["hava_nemi"]   for p in pts_data]
            sics = [p["sicaklik"]    for p in pts_data]

            # ── NEM HARİTASI ──────────────────────────────────────
            if not goster_sicaklik:
                st.markdown('<span class="section-label">💧 İnteraktif Toprak Nemi Dağılımı</span>', unsafe_allow_html=True)

                fig_d = go.Figure()

                fig_d.add_trace(go.Scatter(
                    x=xs, y=ys, mode="lines",
                    line=dict(color="rgba(255,255,255,0.12)", width=1),
                    hoverinfo="skip", name="Drone Yolu"
                ))

                fig_d.add_trace(go.Scatter(
                    x=xs, y=ys, mode="markers",
                    marker=dict(
                        size=16,
                        color=nems,
                        colorscale=[
                            [0.0,  "#b71c1c"],
                            [0.25, "#f44336"],
                            [0.40, "#ff9800"],
                            [0.55, "#ffeb3b"],
                            [0.70, "#66bb6a"],
                            [1.0,  "#1565c0"],
                        ],
                        cmin=0, cmax=100,
                        colorbar=dict(
                            title="Toprak Nemi (%)",
                            tickvals=[0, 25, 40, 55, 70, 100],
                            ticktext=["0% Çok Kurak", "25%", "40% Eşik", "55%", "70%", "100% Nemli"],
                            thickness=16, len=0.85,
                            bgcolor="rgba(17,31,18,0.8)",
                            bordercolor="rgba(93,184,93,0.25)",
                            borderwidth=1,
                            tickfont=dict(color="#aaa"),
                            titlefont=dict(color="#7aaa7d"),
                        ),
                        showscale=True,
                        line=dict(color="rgba(255,255,255,0.3)", width=1),
                    ),
                    customdata=list(zip(hava, sics)),
                    hovertemplate=(
                        "<b>Konum:</b> (%{x:.1f}, %{y:.1f})<br>"
                        "<b>Toprak Nemi:</b> %{marker.color:.1f}%<br>"
                        "<b>Hava Nemi:</b> %{customdata[0]:.1f}%<br>"
                        "<b>Sıcaklık:</b> %{customdata[1]:.1f} °C<extra></extra>"
                    ),
                    name="Toprak Nemi"
                ))

                kurak_pts = [p for p in pts_data if p["toprak_nemi"] < 40]
                if kurak_pts:
                    fig_d.add_trace(go.Scatter(
                        x=[p["x"] for p in kurak_pts],
                        y=[p["y"] for p in kurak_pts],
                        mode="markers",
                        marker=dict(symbol="x", size=20, color="#ff5252", line=dict(width=3, color="#ff1744")),
                        name="⚠️ Kurak Bölge (<40%)",
                        hovertemplate="<b>KURAK BÖLGE</b><extra></extra>"
                    ))

                fig_d.update_layout(
                    plot_bgcolor="rgba(13,26,14,0.97)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#666", title="X Konumu (m)"),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#666", title="Y Konumu (m)", scaleanchor="x"),
                    legend=dict(bgcolor="rgba(17,31,18,0.85)", bordercolor="rgba(93,184,93,0.25)", borderwidth=1, font=dict(color="#bbb", size=11)),
                    height=540,
                    margin=dict(l=20, r=20, t=20, b=20),
                    hovermode="closest",
                )
                st.plotly_chart(fig_d, use_container_width=True)

                # Özet
                kurak_sayisi = len(kurak_pts)
                kurak_oran   = (kurak_sayisi / len(pts_data)) * 100
                risk_renk    = "#f44336" if kurak_oran > 30 else "#ff9800" if kurak_oran > 10 else "#4caf50"
                risk_ikon    = "🔴" if kurak_oran > 30 else "🟡" if kurak_oran > 10 else "🟢"

                st.markdown(f"""
                <div style="background:rgba(22,32,24,0.8);border:1px solid rgba(93,184,93,0.18);
                            border-radius:14px;padding:18px 22px;margin-top:12px;">
                    <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.15em;color:#7aaa7d;text-transform:uppercase;margin-bottom:8px;">
                        Saha Kuraklık Özeti
                    </div>
                    <p style="margin:0;font-size:0.95rem;color:#e8f5e2;">
                    {risk_ikon} Tarlanın <strong style="color:{risk_renk}">%{kurak_oran:.1f}'i</strong>
                    kuraklık eşiğinin altında (&lt;%40 toprak nemi) &nbsp;·&nbsp;
                    {kurak_sayisi} / {len(pts_data)} ölçüm noktası kritik
                    </p>
                </div>
                """, unsafe_allow_html=True)

            # ── SICAKLIK HARİTASI ─────────────────────────────────
            else:
                st.markdown('<span class="section-label">🌡 İnteraktif Sıcaklık Dağılımı</span>', unsafe_allow_html=True)

                sic_min = min(sics)
                sic_max = max(sics)
                sic_ort = sum(sics) / len(sics)

                fig_s = go.Figure()

                fig_s.add_trace(go.Scatter(
                    x=xs, y=ys, mode="lines",
                    line=dict(color="rgba(255,255,255,0.08)", width=1),
                    hoverinfo="skip", name="Drone Yolu"
                ))

                fig_s.add_trace(go.Scatter(
                    x=xs, y=ys, mode="markers",
                    marker=dict(
                        size=16,
                        color=sics,
                        colorscale=[
                            [0.0,  "#1a237e"],
                            [0.2,  "#1565c0"],
                            [0.4,  "#43a047"],
                            [0.6,  "#f9a825"],
                            [0.8,  "#e64a19"],
                            [1.0,  "#b71c1c"],
                        ],
                        cmin=sic_min, cmax=sic_max,
                        colorbar=dict(
                            title="Sıcaklık (°C)",
                            thickness=16, len=0.85,
                            bgcolor="rgba(17,31,18,0.8)",
                            bordercolor="rgba(93,184,93,0.25)",
                            borderwidth=1,
                            tickfont=dict(color="#aaa"),
                            titlefont=dict(color="#c8a96e"),
                        ),
                        showscale=True,
                        line=dict(color="rgba(255,255,255,0.25)", width=1),
                    ),
                    customdata=list(zip(nems, hava)),
                    hovertemplate=(
                        "<b>Konum:</b> (%{x:.1f}, %{y:.1f})<br>"
                        "<b>Sıcaklık:</b> %{marker.color:.1f} °C<br>"
                        "<b>Toprak Nemi:</b> %{customdata[0]:.1f}%<br>"
                        "<b>Hava Nemi:</b> %{customdata[1]:.1f}%<extra></extra>"
                    ),
                    name="Sıcaklık (°C)"
                ))

                # Yüksek sıcaklık uyarısı (>35°C)
                sicak_pts = [p for p in pts_data if p["sicaklik"] > 35]
                if sicak_pts:
                    fig_s.add_trace(go.Scatter(
                        x=[p["x"] for p in sicak_pts],
                        y=[p["y"] for p in sicak_pts],
                        mode="markers",
                        marker=dict(symbol="triangle-up", size=18, color="#ff6d00", line=dict(width=2, color="#fff")),
                        name="🔥 Yüksek Sıcaklık (>35°C)",
                        hovertemplate="<b>YÜKSEK SICAKLIK BÖLGESİ</b><extra></extra>"
                    ))

                fig_s.update_layout(
                    plot_bgcolor="rgba(13,26,14,0.97)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#666", title="X Konumu (m)"),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", color="#666", title="Y Konumu (m)", scaleanchor="x"),
                    legend=dict(bgcolor="rgba(17,31,18,0.85)", bordercolor="rgba(93,184,93,0.25)", borderwidth=1, font=dict(color="#bbb", size=11)),
                    height=540,
                    margin=dict(l=20, r=20, t=20, b=20),
                    hovermode="closest",
                )
                st.plotly_chart(fig_s, use_container_width=True)

                # Sıcaklık Özeti
                sicak_sayisi = len(sicak_pts)
                sicak_oran   = (sicak_sayisi / len(pts_data)) * 100 if pts_data else 0
                risk_renk_s  = "#f44336" if sic_ort > 35 else "#ff9800" if sic_ort > 28 else "#4caf50"
                risk_ikon_s  = "🔴" if sic_ort > 35 else "🟡" if sic_ort > 28 else "🟢"

                col_s1, col_s2, col_s3 = st.columns(3)
                col_s1.metric("🌡 Min Sıcaklık", f"{sic_min:.1f} °C")
                col_s2.metric("🌡 Ort Sıcaklık", f"{sic_ort:.1f} °C")
                col_s3.metric("🌡 Max Sıcaklık", f"{sic_max:.1f} °C")

                if sicak_sayisi > 0:
                    st.markdown(f"""
                    <div style="background:rgba(230,74,25,0.1);border:1px solid rgba(230,74,25,0.3);
                                border-radius:14px;padding:16px 22px;margin-top:12px;">
                        <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.15em;color:#ff8a65;text-transform:uppercase;margin-bottom:8px;">
                            🔥 Sıcaklık Uyarısı
                        </div>
                        <p style="margin:0;font-size:0.95rem;color:#e8f5e2;">
                        {risk_ikon_s} <strong style="color:{risk_renk_s}">{sicak_sayisi} ölçüm noktası</strong>
                        kritik sıcaklığın üzerinde (&gt;35°C) &nbsp;·&nbsp; Tüm alanın %{sicak_oran:.1f}'i etkileniyor
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.success("✅ Tüm ölçüm bölgelerinde sıcaklık normal aralıkta.")

        else:
            st.markdown("""
            <div style="background:rgba(22,32,24,0.7);border:1px solid rgba(93,184,93,0.15);
                        border-radius:16px;padding:32px;text-align:center;">
                <div style="font-size:2rem;margin-bottom:12px;">📡</div>
                <p style="font-size:1rem;color:#7aaa7d;margin:0;">Firebase'de henüz harita verisi yok.</p>
                <p style="font-size:0.82rem;color:#4a7a4d;margin-top:6px;">Drone görevini başlatın; uçuş sırasında her 5 saniyede canlı güncellenir.</p>
            </div>
            """, unsafe_allow_html=True)

        # ── OpenCV PNG ─────────────────────────────────────────────
        if goster_png:
            st.divider()
            st.markdown('<span class="section-label">🖼️ Drone Kuraklık Haritası (OpenCV PNG)</span>', unsafe_allow_html=True)
            with st.spinner("Firebase'den harita PNG indiriliyor..."):
                map_img = get_drought_map_image()
            if map_img:
                st.image(map_img, caption="IDW interpolasyon — final kuraklık haritası", use_container_width=True)
                st.success("✅ Harita başarıyla yüklendi.")
            else:
                st.warning("⚠️ Henüz final harita yüklenmemiş. Drone görevi tamamlandığında görünecek.")
