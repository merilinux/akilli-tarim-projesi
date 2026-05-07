import streamlit as st
from google import genai
from PIL import Image
import pandas as pd
import random
import os
import json
import requests
from datetime import datetime
import plotly.graph_objects as go  # Drone rotası çizimi için

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
FIREBASE_URL = "https://botanix-iot-default-rtdb.europe-west1.firebasedatabase.app/botanix_sensor.json"

def get_sensor_data_from_firebase():
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
                 st.warning("⚠️ Firebase'de veri bulunamadı.")
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
    "TR-1000": {"ad": "Meryem Derin", "telefon": "5550000000", "bahceler": ["Konya Merkez Lale Serası", "Çumra Domates Tesisleri"]},
    "TR-1001": {"ad": "Melih Geylani", "telefon": "5550000001", "bahceler": ["Ereğli Organik Çilek"]},
    "TR-1002": {"ad": "Juri1", "telefon": "000", "bahceler": ["Genel Test Serası"]}
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
        st.markdown('<p style="font-size:0.85rem; opacity:0.75; margin-bottom:16px;">Jüri üyeleri ve test amaçlı ziyaretler için.</p>', unsafe_allow_html=True)
        if st.button("→ Misafir Olarak Devam Et", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.is_guest = True
            st.session_state.user_id = f"GUEST-{random.randint(1000, 9999)}"
            st.session_state.user_name = "Misafir Ziyaretçi"
            st.session_state.kullanici_bahceleri = ["Misafir Test Serası"]
            st.session_state.aktif_bahce = "Misafir Test Serası"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📝 Sistemi Kullanmaya Başlayın: Yeni Çiftçi Kaydı Oluştur", expanded=False):
        st.markdown('<span class="section-label">Ücretsiz Ön Kayıt</span>', unsafe_allow_html=True)
        
        yeni_ad = st.text_input("Ad - Soyad", placeholder="Örn: Meryem Derin")
        yeni_tel = st.text_input("Telefon Numarası", placeholder="Örn: 0555 123 4567")
        yeni_bahce = st.text_input("İlk Saha/Sera Adı", placeholder="Örn: Konya Merkez Lale Serası")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_bosluk1, col_buton, col_bosluk2 = st.columns([1, 2, 1])
        with col_buton:
            kayit_tiklandi = st.button("Sisteme Kayıt Ol", use_container_width=True)
            
        if kayit_tiklandi:
            if yeni_ad and yeni_tel and yeni_bahce:
                temiz_yeni_tel = yeni_tel.replace(" ", "")
                numara_kayitli_mi = False
                kayitli_id = ""

                for uid, veriler in GUNCEL_KULLANICILAR.items():
                    if veriler.get("telefon", "").replace(" ", "") == temiz_yeni_tel:
                        numara_kayitli_mi = True
                        kayitli_id = uid
                        break

                if numara_kayitli_mi:
                    st.error(f"🚨 HATA: Bu telefon numarası sisteme zaten kayıtlı! Lütfen Müşteri ID'niz (**{kayitli_id}**) ile yukarıdan giriş yapınız.")
                else:
                    while True:
                        yeni_id = f"TR-{random.randint(2000, 9999)}"
                        if yeni_id not in GUNCEL_KULLANICILAR:
                            break
                    
                    GUNCEL_KULLANICILAR[yeni_id] = {
                        "ad": yeni_ad, "telefon": temiz_yeni_tel, "bahceler": [yeni_bahce]
                    }
                    save_users(GUNCEL_KULLANICILAR)
                    st.success(f"🎉 Kayıt Başarılı! Sisteme Giriş ID'niz: **{yeni_id}**")
                    st.info("Lütfen bu ID'yi not alın. Sayfayı yenileyip yukarıdaki 'Kayıtlı Çiftçi Girişi' panelinden giriş yapabilirsiniz.")
            else:
                st.warning("Lütfen tüm alanları eksiksiz doldurunuz.")

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
        secilen = st.selectbox("Aktif Saha", options=st.session_state.kullanici_bahceleri,
                               index=st.session_state.kullanici_bahceleri.index(st.session_state.aktif_bahce) if st.session_state.aktif_bahce in st.session_state.kullanici_bahceleri else 0,
                               label_visibility="collapsed")
        
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
            (genel_veritabani["Bahçe/Sera"] == st.session_state.aktif_bahce)
        ]
