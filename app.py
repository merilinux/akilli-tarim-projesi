import streamlit as st
from google import genai
from PIL import Image
import pandas as pd
import random
import os
import json
import requests
from datetime import datetime

# ==========================================
# SAYFA AYARLARI VE ELİT TASARIM (CSS)
# ==========================================
st.set_page_config(page_title="Botanix — Akıllı Tarım", layout="wide", page_icon="🌿")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #0d1a0e;
        color: #e8f5e9;
    }

    /* ARKA PLAN */
    .stApp {
        background: linear-gradient(135deg, #0d1a0e 0%, #0f2311 40%, #0a1a10 100%);
        background-attachment: fixed;
    }

    /* BAŞLIKLAR */
    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif;
        color: #a5d6a7;
        letter-spacing: -0.02em;
    }

    /* ANA TITLE */
    .stApp > header + div h1 {
        font-size: 2.6rem;
        background: linear-gradient(90deg, #81c784, #c8e6c9, #66bb6a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* TAB STİLİ */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.04);
        border-radius: 14px;
        padding: 6px;
        gap: 4px;
        border: 1px solid rgba(165,214,167,0.15);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 22px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        font-size: 0.88rem;
        color: #81c784;
        background: transparent;
        transition: all 0.25s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2e7d32, #388e3c) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 20px rgba(46,125,50,0.4);
    }

    /* METRİK KUTULARI */
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(46,125,50,0.15), rgba(27,94,32,0.08));
        border: 1px solid rgba(165,214,167,0.2);
        border-radius: 16px;
        padding: 20px 24px;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(46,125,50,0.25);
    }
    [data-testid="stMetricLabel"] {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #81c784 !important;
        opacity: 0.85;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem !important;
        color: #c8e6c9 !important;
        font-weight: 700;
    }

    /* BUTONLAR */
    .stButton > button {
        background: linear-gradient(135deg, #2e7d32, #43a047);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        padding: 12px 28px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.03em;
        transition: all 0.25s ease;
        box-shadow: 0 4px 15px rgba(46,125,50,0.3);
        position: relative;
        overflow: hidden;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #388e3c, #4caf50);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(46,125,50,0.45);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1f0b 0%, #0d2610 100%) !important;
        border-right: 1px solid rgba(165,214,167,0.12);
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #66bb6a;
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        margin-bottom: 8px;
    }
    [data-testid="stSidebarContent"] {
        padding: 24px 16px;
    }

    /* INPUT ALANLARI */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(165,214,167,0.25) !important;
        border-radius: 10px !important;
        color: #e8f5e9 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(165,214,167,0.6) !important;
        box-shadow: 0 0 0 2px rgba(165,214,167,0.1) !important;
    }

    /* SLIDERS */
    .stSlider [data-baseweb="slider"] {
        padding-top: 8px;
    }
    .stSlider [data-baseweb="thumb"] {
        background: #4caf50 !important;
        border: 2px solid #a5d6a7 !important;
    }
    .stSlider [data-baseweb="track-inner"] {
        background: linear-gradient(90deg, #2e7d32, #66bb6a) !important;
    }

    /* UYARI / BİLGİ KUTULARI */
    .stSuccess > div {
        background: rgba(46,125,50,0.2) !important;
        border: 1px solid rgba(102,187,106,0.4) !important;
        border-radius: 12px !important;
        color: #a5d6a7 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stError > div {
        background: rgba(183,28,28,0.2) !important;
        border: 1px solid rgba(229,115,115,0.4) !important;
        border-radius: 12px !important;
        color: #ef9a9a !important;
    }
    .stWarning > div {
        background: rgba(230,162,0,0.12) !important;
        border: 1px solid rgba(255,202,40,0.3) !important;
        border-radius: 12px !important;
        color: #ffe082 !important;
    }
    .stInfo > div {
        background: rgba(1,87,155,0.2) !important;
        border: 1px solid rgba(79,195,247,0.3) !important;
        border-radius: 12px !important;
        color: #81d4fa !important;
    }

    /* EXPANDER */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(165,214,167,0.18) !important;
        border-radius: 12px !important;
        color: #a5d6a7 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
    }
    .streamlit-expanderContent {
        border: 1px solid rgba(165,214,167,0.12) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        background: rgba(0,0,0,0.2) !important;
    }

    /* DATAFRAME */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(165,214,167,0.15);
    }

    /* DIVIDER */
    hr {
        border: none !important;
        border-top: 1px solid rgba(165,214,167,0.12) !important;
        margin: 24px 0 !important;
    }

    /* UPLOAD */
    [data-testid="stUploadedFile"] { display: none !important; }
    .css-1g5m0rc.e1b2p2ww12 { display: none; }

    /* HASTALIK ALARM */
    .hastalik-alarm {
        background: linear-gradient(135deg, rgba(183,28,28,0.25), rgba(183,28,28,0.1));
        padding: 20px 24px;
        border-radius: 14px;
        border-left: 4px solid #ef5350;
        color: #ef9a9a;
        font-weight: 600;
        font-family: 'DM Sans', sans-serif;
        letter-spacing: 0.02em;
        margin-bottom: 20px;
        backdrop-filter: blur(8px);
    }

    /* LOGIN KUTUSU */
    .login-box {
        background: linear-gradient(135deg, rgba(46,125,50,0.15), rgba(27,94,32,0.08));
        padding: 48px 40px;
        border-radius: 24px;
        border: 1px solid rgba(165,214,167,0.2);
        text-align: center;
        margin-bottom: 32px;
        backdrop-filter: blur(12px);
    }
    .login-box h1 {
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem;
        background: linear-gradient(90deg, #81c784, #c8e6c9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 12px;
    }
    .login-box p {
        color: #81c784;
        font-size: 0.95rem;
        opacity: 0.8;
    }

    /* GİRİŞ KART KUTULARI */
    .login-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(165,214,167,0.15);
        border-radius: 18px;
        padding: 28px 24px;
        transition: border-color 0.3s ease;
    }
    .login-card:hover {
        border-color: rgba(165,214,167,0.35);
    }

    /* BÖLÜM BAŞLIKLARI */
    .section-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #66bb6a;
        margin-bottom: 12px;
        display: block;
        opacity: 0.9;
    }

    /* SUBHEADER OVERRIDE */
    .stApp [data-testid="stMarkdownContainer"] h3 {
        font-size: 1.05rem;
        font-weight: 600;
        color: #a5d6a7;
        border-bottom: 1px solid rgba(165,214,167,0.12);
        padding-bottom: 8px;
        margin-bottom: 16px;
    }

    /* RADYO BUTONLARI */
    .stRadio > div {
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        padding: 8px 12px;
        border: 1px solid rgba(165,214,167,0.12);
    }
    .stRadio label {
        color: #c8e6c9 !important;
    }

    /* SELECTBOX */
    [data-baseweb="select"] {
        background: rgba(255,255,255,0.05) !important;
    }

    /* PROGRESS */
    .stProgress .st-bo {
        background: linear-gradient(90deg, #2e7d32, #66bb6a) !important;
    }

    /* GENEL METİN */
    p, li, label, .stMarkdown {
        color: #c8e6c9;
        line-height: 1.65;
    }

    /* SPINNER */
    .stSpinner > div {
        border-top-color: #66bb6a !important;
    }

    /* CAMERA */
    .stCameraInput {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(165,214,167,0.2);
    }

    /* SCROLLBAR */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
    ::-webkit-scrollbar-thumb { background: rgba(102,187,106,0.4); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(102,187,106,0.6); }

    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FIREBASE AYARLARI
# ==========================================
FIREBASE_URL = "https://botanix-iot-default-rtdb.europe-west1.firebasedatabase.app/botanix_sensor.json"

def get_sensor_data_from_firebase():
    """Buluttaki veritabanından ESP32'nin son ölçümlerini okur."""
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            data = response.json()
            if data:
                return {
                    "soil": data.get("toprak_nemi", 0), 
                    "temp": data.get("ortam_sicakligi", 25),
                    "hum": data.get("hava_nemi", 55)
                }
            else:
                 st.warning("⚠️ Firebase'de veri bulunamadı. Lütfen ESP32'nin çalıştığından emin olun.")
        else:
             st.error(f"⚠️ Firebase Bağlantı Hatası: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Sunucuya erişilemiyor: {e}")
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
    "TR-1000": {"ad": "Meryem Derin", "bahceler": ["Konya Merkez Lale Serası", "Çumra Domates Tesisleri"]},
    "TR-1001": {"ad": "Melih Geylani", "bahceler": ["Ereğli Organik Çilek"]},
    "TR-1002": {"ad": "Juri1", "bahceler": ["Genel Test Serası"]},
    "TR-1003": {"ad": "Juri2", "bahceler": ["Genel Test Serası"]},
    "TR-1004": {"ad": "Juri3", "bahceler": ["Genel Test Serası"]}
}

def load_and_sync_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_USERS, f, ensure_ascii=False, indent=4)
        return DEFAULT_USERS
    
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        kayitli_kullanicilar = json.load(f)
        
    guncellendi_mi = False
    
    for user_id, data in DEFAULT_USERS.items():
        if user_id not in kayitli_kullanicilar:
            kayitli_kullanicilar[user_id] = data
            guncellendi_mi = True
        else:
            if kayitli_kullanicilar[user_id]["ad"] != data["ad"]:
                kayitli_kullanicilar[user_id]["ad"] = data["ad"]
                guncellendi_mi = True
            for bahce in data["bahceler"]:
                if bahce not in kayitli_kullanicilar[user_id]["bahceler"]:
                    kayitli_kullanicilar[user_id]["bahceler"].append(bahce)
                    guncellendi_mi = True
                    
    silinecek_idler = [uid for uid in kayitli_kullanicilar if uid not in DEFAULT_USERS]
    for uid in silinecek_idler:
        del kayitli_kullanicilar[uid]
        guncellendi_mi = True

    if guncellendi_mi:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(kayitli_kullanicilar, f, ensure_ascii=False, indent=4)
            
    return kayitli_kullanicilar

def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=4)

GUNCEL_KULLANICILAR = load_and_sync_users()

# ==========================================
# OTURUM (SESSION) YÖNETİMİ
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "aktif_bahce" not in st.session_state:
    st.session_state.aktif_bahce = ""
if "kullanici_bahceleri" not in st.session_state:
    st.session_state.kullanici_bahceleri = []
if "is_guest" not in st.session_state:
    st.session_state.is_guest = False
if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = {"temp": 0, "hum": 0, "soil": 0}

# ==========================================
# EKRAN 1: GİRİŞ EKRANI (LOGIN)
# ==========================================
if not st.session_state.logged_in:
    st.markdown("""
    <div class="login-box">
        <h1>🌿 Botanix</h1>
        <p>Otonom Tarım Yönetim Platformu — Giriş yapın veya misafir olarak devam edin.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<span class="section-label">🧑‍🌾 Kayıtlı Çiftçi Girişi</span>', unsafe_allow_html=True)
        girilen_id = st.text_input("Müşteri ID", placeholder="Örn: TR-1000", key="login_id", label_visibility="collapsed").strip().upper()
        if st.button("→ Sisteme Giriş Yap", use_container_width=True):
            if girilen_id in GUNCEL_KULLANICILAR:
                st.session_state.logged_in = True
                st.session_state.is_guest = False
                st.session_state.user_id = girilen_id
                st.session_state.user_name = GUNCEL_KULLANICILAR[girilen_id]["ad"]
                st.session_state.kullanici_bahceleri = GUNCEL_KULLANICILAR[girilen_id]["bahceler"]
                st.session_state.aktif_bahce = st.session_state.kullanici_bahceleri[0]
                st.rerun()
            else:
                st.error("❌ Kayıtlı kullanıcı bulunamadı.")
        st.markdown('</div>', unsafe_allow_html=True)
                
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<span class="section-label">🔍 Misafir / Ziyaretçi Girişi</span>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.85rem; color:#81c784; opacity:0.75; margin-bottom:16px;">QR kod ile bağlanan ziyaretçiler ve jüri üyeleri bu seçeneği kullanabilir.</p>', unsafe_allow_html=True)
        if st.button("→ Misafir Olarak Devam Et", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.is_guest = True
            st.session_state.user_id = f"GUEST-{random.randint(1000, 9999)}"
            st.session_state.user_name = "Misafir Ziyaretçi"
            st.session_state.kullanici_bahceleri = ["Misafir Test Serası"]
            st.session_state.aktif_bahce = "Misafir Test Serası"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# EKRAN 2: ANA UYGULAMA (GİRİŞ YAPILDIYSA)
# ==========================================
else:
    with st.sidebar:
        # Profil
        st.markdown(f"""
        <div style="background:rgba(46,125,50,0.15);border:1px solid rgba(165,214,167,0.2);
                    border-radius:14px;padding:16px;margin-bottom:16px;">
            <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;
                        color:#66bb6a;font-weight:600;margin-bottom:6px;">Aktif Oturum</div>
            <div style="font-size:1.05rem;font-weight:600;color:#c8e6c9;margin-bottom:2px;">
                {st.session_state.user_name}
            </div>
            <div style="font-size:0.78rem;color:#81c784;opacity:0.7;">{st.session_state.user_id}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<span class="section-label">🏡 Saha / Sera Seçimi</span>', unsafe_allow_html=True)
        secilen = st.selectbox(
            "Aktif Saha",
            options=st.session_state.kullanici_bahceleri,
            index=st.session_state.kullanici_bahceleri.index(st.session_state.aktif_bahce) if st.session_state.aktif_bahce in st.session_state.kullanici_bahceleri else 0,
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
        except:
            api_key = None
            st.error("⚠️ API Anahtarı Eksik")

    # BAŞLIK
    st.markdown(f"""
    <div style="margin-bottom:8px;">
        <h1 style="margin-bottom:4px;">🌿 Botanix</h1>
        <div style="font-size:0.85rem;color:#81c784;opacity:0.75;letter-spacing:0.04em;">
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
            (genel_veritabani["Bahçe/Sera"] == st.session_state.aktif_bahce)
        ]

    tab1, tab2, tab3 = st.tabs(["📸  Anlık Analiz", "📅  Gelişim Ajandası", "🔮  Proaktif Risk Tahmini"])

    # ------------------------------------------
    # SEKME 1: ANLIK ANALİZ
    # ------------------------------------------
    with tab1:
        st.markdown(f'<span class="section-label">📡 IoT Sensör Ağı — {st.session_state.aktif_bahce}</span>', unsafe_allow_html=True)

        if st.button("📡 ESP32 Sensör Verilerini Çek", use_container_width=False):
            with st.spinner("Bulut üzerinden ESP32 ile haberleşiliyor..."):
                gercek_veri = get_sensor_data_from_firebase()
                if gercek_veri:
                    st.session_state.sensor_data = gercek_veri
                    st.success(f"✅ Güncel veriler alındı.")
                else:
                    st.error("ESP32 verisi alınamadı.")

        met_col1, met_col2, met_col3 = st.columns(3)
        met_col1.metric(label="🌡 Ortam Sıcaklığı", value=f"{st.session_state.sensor_data['temp']} °C")
        met_col2.metric(label="💧 Hava Nemi", value=f"%{st.session_state.sensor_data['hum']}")
        met_col3.metric(label="🌱 Toprak Nemi", value=f"%{st.session_state.sensor_data['soil']}")
        
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
                        c_hum = st.session_state.sensor_data['hum']
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

                        response = client.models.generate_content(
                            model='gemini-2.5-flash-lite',
                            contents=[prompt, image]
                        )
                        response_text = response.text

                        if "[SAHTE]" in response_text:
                            st.error("🚨 UYARI: Görüntüdeki bitki SUNİ/PLASTİK olarak tespit edildi! Kayıt engellendi.")
                        elif "[GERÇEK]" in response_text:
                            st.success(f"✅ Analiz tamamlandı — {st.session_state.aktif_bahce}")
                            st.markdown(response_text.replace("[GERÇEK]", "").strip())

                            if not st.session_state.is_guest:
                                new_data = pd.DataFrame({
                                    "Kullanıcı ID": [st.session_state.user_id],
                                    "Kullanıcı Adı": [st.session_state.user_name],
                                    "Bahçe/Sera": [st.session_state.aktif_bahce],
                                    "Tarih": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                                    "Ortam Sıcaklığı (°C)": [c_temp],
                                    "Hava Nemi (%)": [c_hum],
                                    "Toprak Nemi (%)": [c_soil]
                                })
                                save_to_database(new_data)
                                st.info("💾 Analiz sonucu veritabanına kalıcı olarak kaydedildi.")
                            else:
                                st.warning("⚠️ Misafir oturumunda kayıt tutulmamaktadır.")
                        else:
                            st.markdown(response_text)
                    except Exception as e:
                        st.error(f"Sistem Hatası: {e}")

    # ------------------------------------------
    # SEKME 2: AJANDA
    # ------------------------------------------
    with tab2:
        st.markdown(f'<span class="section-label">📅 Kalıcı Veri Tabanı — {st.session_state.aktif_bahce}</span>', unsafe_allow_html=True)
        
        if st.session_state.is_guest:
            st.warning("Misafir oturumlarında kayıt tutulmaz. Geçmişe erişmek için Çiftçi ID'niz ile giriş yapın.")
        else:
            guncel_veritabani = load_database()
            kullanici_guncel_veri = guncel_veritabani[
                (guncel_veritabani["Kullanıcı ID"] == st.session_state.user_id) & 
                (guncel_veritabani["Bahçe/Sera"] == st.session_state.aktif_bahce)
            ]
            
            st.markdown(f'<p style="font-size:0.88rem;color:#81c784;opacity:0.8;">**{st.session_state.aktif_bahce}** bölgesi için kaydedilen sensör okumalarının zaman serisi.</p>', unsafe_allow_html=True)
            
            if not kullanici_guncel_veri.empty:
                st.dataframe(kullanici_guncel_veri, use_container_width=True)
                st.divider()
                st.markdown('<span class="section-label">📉 Zaman Serisi Analizi</span>', unsafe_allow_html=True)
                chart_data = kullanici_guncel_veri.set_index("Tarih")[["Ortam Sıcaklığı (°C)", "Hava Nemi (%)", "Toprak Nemi (%)"]]
                st.line_chart(chart_data)
            else:
                st.info(f"ℹ️ {st.session_state.aktif_bahce} için henüz kayıt yok. İlk analizi 'Anlık Analiz' sekmesinden başlatın.")

    # ------------------------------------------
    # SEKME 3: SİMÜLASYON VE ERKEN UYARI
    # ------------------------------------------
    with tab3:
        st.markdown(f'<span class="section-label">🔮 Proaktif Karar Destek — {st.session_state.aktif_bahce}</span>', unsafe_allow_html=True)
        col3, col4 = st.columns(2, gap="large")
        with col3:
            sim_temp = st.slider("Tahmini Sıcaklık (°C)", 10.0, 50.0, 32.0, step=0.5, key="sim_temp")
            sim_hum = st.slider("Tahmini Hava Nemi (%)", 0.0, 100.0, 85.0, step=1.0, key="sim_hum")
        with col4:
            sim_soil = st.slider("Tahmini Toprak Nemi (%)", 0.0, 100.0, 15.0, step=1.0, key="sim_soil")
            sim_days = st.selectbox("Tahmin Ufku (Gün)", [1,3,4,5,6,7,8,9,10,11,12,13,14], key="sim_days")

        if st.button(f"⏳ {sim_days} Günlük Senaryoyu Simüle Et", use_container_width=True):
            if not api_key:
                st.error("⚠️ API Anahtarı eksik!")
            else:
                with st.spinner("Senaryo hesaplanıyor..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        guncel_db = load_database()
                        guncel_gecmis = guncel_db[
                            (guncel_db["Kullanıcı ID"] == st.session_state.user_id) & 
                            (guncel_db["Bahçe/Sera"] == st.session_state.aktif_bahce)
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
                        sim_text = sim_response.text

                        if "[HASTALIK_ALARM:" in sim_text:
                            start_idx = sim_text.find("[HASTALIK_ALARM:") + 16
                            end_idx = sim_text.find("]", start_idx)
                            hastalik_adi = sim_text[start_idx:end_idx].strip()
                            st.markdown(f'<div class="hastalik-alarm">🚨 KRİTİK ERKEN UYARI — {hastalik_adi} tehlikesi tespit edildi!</div>', unsafe_allow_html=True)
                            st.markdown(sim_text[end_idx+1:].strip())
                        else:
                            st.success("✅ Risk tespit edilmedi.")
                            st.markdown(sim_text)
                    except Exception as e:
                        st.error(f"Hata: {e}")
