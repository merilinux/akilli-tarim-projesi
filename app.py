import streamlit as st
from google import genai
from PIL import Image
import pandas as pd
import random
import os
import json
from datetime import datetime

# ==========================================
# SAYFA AYARLARI VE RESMİ TASARIM (CSS)
# ==========================================
st.set_page_config(page_title="Akıllı Tarım ve Otonom Sulama", layout="wide", page_icon="🌱")

st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    h1, h2, h3 {
        color: #1e4620;
        font-family: 'Georgia', serif;
    }
    .stProgress .st-bo {
        background-color: #4CAF50;
    }
    .hastalik-alarm {
        background-color: #ffcccc;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid red;
        color: #900000;
        font-weight: bold;
        margin-bottom: 20px;
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #2e7d32;
    }
    [data-testid="stUploadedFile"] {
        display: none !important;
    }
    .css-1g5m0rc.e1b2p2ww12 {
        display: none;
    }
    .login-box {
        background-color: #f1f8e9;
        padding: 30px;
        border-radius: 15px;
        border: 2px solid #81c784;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

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

# BURAYI İSTEDİĞİN ZAMAN GÜNCELLEYEBİLİRSİN!
DEFAULT_USERS = {
    "TR-1000": {"ad": "Meryem Derin", "bahceler": ["Konya Merkez Lale Serası", "Çumra Domates Tesisleri"]},
    "TR-1001": {"ad": "Melih Geylani", "bahceler": ["Ereğli Organik Çilek"]},
    "TR-1002": {"ad": "Juri1", "bahceler": ["Genel Test Serası"]},
    "TR-1003": {"ad": "Juri2", "bahceler": ["Genel Test Serası"]},
    "TR-1004": {"ad": "Juri3", "bahceler": ["Genel Test Serası"]}
}

def load_and_sync_users():
    """Koddaki listeyi, dosyadaki listeyle akıllıca birleştirir."""
    # 1. Eğer dosya hiç yoksa, direkt koddakini yaz ve dön
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_USERS, f, ensure_ascii=False, indent=4)
        return DEFAULT_USERS
    
    # 2. Dosya varsa oku
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        kayitli_kullanicilar = json.load(f)
        
    guncellendi_mi = False
    
    # 3. Koddaki yeni kişileri veya isim değişikliklerini dosyaya aktar
    for user_id, data in DEFAULT_USERS.items():
        if user_id not in kayitli_kullanicilar:
            # Yeni bir ID eklenmiş!
            kayitli_kullanicilar[user_id] = data
            guncellendi_mi = True
        else:
            # ID var ama adı değişmiş olabilir (Örn: Juri1 -> Ahmet Hoca)
            if kayitli_kullanicilar[user_id]["ad"] != data["ad"]:
                kayitli_kullanicilar[user_id]["ad"] = data["ad"]
                guncellendi_mi = True
            
            # Koddaki yeni bahçeleri de ekle (Kullanıcının kendi eklediği bahçeleri silmeden!)
            for bahce in data["bahceler"]:
                if bahce not in kayitli_kullanicilar[user_id]["bahceler"]:
                    kayitli_kullanicilar[user_id]["bahceler"].append(bahce)
                    guncellendi_mi = True
                    
    # 4. KODDAN SİLİNEN kişileri dosyadan da sil
    silinecek_idler = [uid for uid in kayitli_kullanicilar if uid not in DEFAULT_USERS]
    for uid in silinecek_idler:
        del kayitli_kullanicilar[uid]
        guncellendi_mi = True

    # 5. Eğer bir değişiklik olduysa dosyayı ez/kaydet
    if guncellendi_mi:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(kayitli_kullanicilar, f, ensure_ascii=False, indent=4)
            
    return kayitli_kullanicilar

def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=4)

# Uygulama başlarken kullanıcıları eşitle
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
    st.session_state.sensor_data = {"temp": 24, "hum": 50, "soil": 40}

# ==========================================
# EKRAN 1: GİRİŞ EKRANI (LOGIN)
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="login-box"><h1>🌱 Akıllı Tarım SaaS Platformuna Hoş Geldiniz</h1><p>Lütfen devam etmek için giriş yöntemi seçin.</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧑‍🌾 Kayıtlı Çiftçi Girişi")
        st.info("Sisteme tanımlı Müşteri ID'nizi giriniz. (Örn: TR-1000)")
        girilen_id = st.text_input("Müşteri ID:", key="login_id").strip().upper()
        
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if girilen_id in GUNCEL_KULLANICILAR:
                st.session_state.logged_in = True
                st.session_state.is_guest = False
                st.session_state.user_id = girilen_id
                st.session_state.user_name = GUNCEL_KULLANICILAR[girilen_id]["ad"]
                st.session_state.kullanici_bahceleri = GUNCEL_KULLANICILAR[girilen_id]["bahceler"]
                st.session_state.aktif_bahce = st.session_state.kullanici_bahceleri[0]
                st.rerun()
            else:
                st.error("❌ Hatalı ID! Kayıtlı bir kullanıcı bulunamadı.")
                
    with col2:
        st.subheader("🔍 Misafir / Ziyaretçi Girişi")
        st.warning("QR Kod üzerinden bağlanan ziyaretçilerimiz ve jüri üyelerimiz test ortamı için bu seçeneği kullanabilir.")
        if st.button("Misafir Olarak Devam Et", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.is_guest = True
            st.session_state.user_id = f"GUEST-{random.randint(1000, 9999)}"
            st.session_state.user_name = "Misafir Ziyaretçi"
            st.session_state.kullanici_bahceleri = ["Misafir Test Serası"]
            st.session_state.aktif_bahce = "Misafir Test Serası"
            st.rerun()

# ==========================================
# EKRAN 2: ANA UYGULAMA (GİRİŞ YAPILDIYSA)
# ==========================================
else:
    # --- YAN MENÜ VE BAHÇE YÖNETİMİ ---
    with st.sidebar:
        st.header("👤 Profil Bilgileri")
        st.success(f"Hoş geldin, **{st.session_state.user_name}**")
        st.write(f"**ID:** {st.session_state.user_id}")
        
        st.divider()
        st.header("🏡 Saha/Sera Yönetimi")
        
        secilen = st.selectbox(
            "Aktif Saha Seçiniz:", 
            options=st.session_state.kullanici_bahceleri,
            index=st.session_state.kullanici_bahceleri.index(st.session_state.aktif_bahce) if st.session_state.aktif_bahce in st.session_state.kullanici_bahceleri else 0
        )
        
        if secilen != st.session_state.aktif_bahce:
            st.session_state.aktif_bahce = secilen
            st.rerun()

        if not st.session_state.is_guest:
            with st.expander("➕ Yeni Saha/Bölge Ekle"):
                yeni_bahce_adi = st.text_input("Yeni Bölge Adı (Örn: Yonca Tarlası)")
                if st.button("Ekle", use_container_width=True):
                    if yeni_bahce_adi and yeni_bahce_adi not in st.session_state.kullanici_bahceleri:
                        st.session_state.kullanici_bahceleri.append(yeni_bahce_adi)
                        st.session_state.aktif_bahce = yeni_bahce_adi
                        
                        GUNCEL_KULLANICILAR[st.session_state.user_id]["bahceler"].append(yeni_bahce_adi)
                        save_users(GUNCEL_KULLANICILAR)
                        
                        st.success(f"{yeni_bahce_adi} başarıyla eklendi ve sisteme kaydedildi!")
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
        st.header("⚙️ Sistem Ayarları")
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("🔑 API Bağlantısı Aktif")
        except:
            api_key = None
            st.error("⚠️ API Anahtarı Bulunamadı!")

    st.title(f"🌱 Akıllı Tarım Platformu")
    
    genel_veritabani = load_database()
    
    if st.session_state.is_guest:
        kullanici_verisi = pd.DataFrame(columns=genel_veritabani.columns)
    else:
        kullanici_verisi = genel_veritabani[
            (genel_veritabani["Kullanıcı ID"] == st.session_state.user_id) & 
            (genel_veritabani["Bahçe/Sera"] == st.session_state.aktif_bahce)
        ]

    tab1, tab2, tab3 = st.tabs(["📸 Anlık Analiz ve Veri Füzyonu", "📅 Gelişim Ajandası", "🔮 Proaktif Risk Tahmini"])

    # ------------------------------------------
    # SEKME 1: ANLIK ANALİZ
    # ------------------------------------------
    with tab1:
        st.subheader(f"📊 IoT Sensör Ağı Canlı Akışı: {st.session_state.aktif_bahce}")
        
        if st.button("📡 ESP32 Sensör Verilerini Çek"):
            st.session_state.sensor_data = {
                "temp": random.randint(10, 42),
                "hum": random.randint(20, 95),
                "soil": random.randint(10, 90)
            }
            st.success(f"✅ {st.session_state.aktif_bahce} sensörlerinden güncel veriler çekildi!")

        met_col1, met_col2, met_col3 = st.columns(3)
        met_col1.metric(label="🌡 Ortam Sıcaklığı", value=f"{st.session_state.sensor_data['temp']} °C")
        met_col2.metric(label="💧 Hava Nemi", value=f"%{st.session_state.sensor_data['hum']}")
        met_col3.metric(label="🌱 Toprak Nemi", value=f"%{st.session_state.sensor_data['soil']}")
        
        st.divider()

        st.subheader("📷 ESP32-CAM Otonom Görüntü Girişi")
        image = None
        
        with st.expander("Görsel Girişi", expanded=False):
            gorsel_secimi = st.radio("Analiz için görüntü kaynağı seçin:", ["📸 Canlı Kamera", "📁 Sistemden Yükle (Gizli)"], horizontal=True)
            
            if gorsel_secimi == "📸 Canlı Kamera":
                kamera_fotosu = st.camera_input("Bitkinin fotoğrafını çekin")
                if kamera_fotosu:
                    image = Image.open(kamera_fotosu)
                    st.success("✅ Canlı görüntü başarıyla yakalandı! Sekmeyi kapatabilirsiniz.")
                    
            elif gorsel_secimi == "📁 Sistemden Yükle (Gizli)":
                uploaded_file = st.file_uploader("Sisteme fotoğraf aktarın", type=["jpg", "png", "jpeg"])
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.success("✅ Görüntü başarıyla aktarıldı! Sekmeyi kapatabilirsiniz.")
                    st.image(image, caption=f"{st.session_state.aktif_bahce} - Analiz Görüntüsü", width="stretch")

        st.divider()

        st.subheader("🤖 Multimodal Yapay Zekâ Analizi")
        
        if st.button(f"{st.session_state.aktif_bahce} Verilerini Sentezle ve Karar Al", use_container_width=True):
            if not api_key:
                st.error("⚠️ Sistem API Anahtarı eksik!")
            elif not image:
                st.warning("⚠️ Lütfen analiz için görüntü sağlayın.")
            else:
                with st.spinner("Sentezleniyor... Lütfen bekleyin..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        past_data_str = kullanici_verisi.to_string(index=False) if not kullanici_verisi.empty else "Henüz bu bahçe için geçmiş veri yok."
                        
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
                            st.error("🚨 UYARI: Sistem görüntüdeki bitkinin SUNİ (YAPAY) veya PLASTİK olduğunu tespit etti! Veritabanı kaydı engellendi.")
                        elif "[GERÇEK]" in response_text:
                            st.success(f"✅ Başarılı. {st.session_state.aktif_bahce} için analiz tamamlandı.")
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
                                st.info("💾 Analiz sonucu GÜVENLİ VERİTABANINA KALICI OLARAK kaydedildi.")
                            else:
                                st.warning("⚠️ Misafir oturumunda olduğunuz için bu analiz sonucu veritabanına KALICI OLARAK KAYDEDİLMEDİ.")
                        else:
                            st.markdown(response_text)
                    except Exception as e:
                        st.error(f"Sistem Hatası: {e}")

    # ------------------------------------------
    # SEKME 2: AJANDA
    # ------------------------------------------
    with tab2:
        st.subheader(f"📅 Kalıcı Veri Tabanı: {st.session_state.aktif_bahce}")
        
        if st.session_state.is_guest:
            st.warning("Misafir oturumlarında veritabanı kayıt tutmamaktadır. Kayıt tutabilmek için Çiftçi ID'niz ile giriş yapmalısınız.")
        else:
            guncel_veritabani = load_database()
            kullanici_guncel_veri = guncel_veritabani[
                (guncel_veritabani["Kullanıcı ID"] == st.session_state.user_id) & 
                (guncel_veritabani["Bahçe/Sera"] == st.session_state.aktif_bahce)
            ]
            
            st.write(f"Sayın **{st.session_state.user_name}**, aşağıda sadece **{st.session_state.aktif_bahce}** bölgeniz için kaydedilen kalıcı sensör okumaları listelenmektedir.")
            
            if not kullanici_guncel_veri.empty:
                st.dataframe(kullanici_guncel_veri, use_container_width=True)
                st.divider()
                st.subheader("📉 Çevresel Parametrelerin Zaman Serisi Analizi")
                chart_data = kullanici_guncel_veri.set_index("Tarih")[["Ortam Sıcaklığı (°C)", "Hava Nemi (%)", "Toprak Nemi (%)"]]
                st.line_chart(chart_data)
            else:
                st.info(f"ℹ️ Henüz {st.session_state.aktif_bahce} için kaydedilmiş bir geçmiş veri bulunmamaktadır. İlk analizi 'Anlık Analiz' sekmesinden yapabilirsiniz.")

    # ------------------------------------------
    # SEKME 3: SİMÜLASYON VE ERKEN UYARI
    # ------------------------------------------
    with tab3:
        st.subheader(f"🔮 Proaktif Karar Destek: {st.session_state.aktif_bahce}")
        col3, col4 = st.columns(2)
        with col3:
            sim_temp = st.slider("Tahmini Gelecek Sıcaklık (°C)", 10.0, 50.0, 32.0, step=0.5, key="sim_temp")
            sim_hum = st.slider("Tahmini Hava Nemi (%)", 0.0, 100.0, 85.0, step=1.0, key="sim_hum")
        with col4:
            sim_soil = st.slider("Tahmini Toprak Nemi (%)", 0.0, 100.0, 15.0, step=1.0, key="sim_soil")
            sim_days = st.selectbox("Kaç Gün Sonrası İçin Tahmin Yapılsın?", [1,3,4,5,6,7,8,9,10,11,12,13,14], key="sim_days")

        if st.button(f"⏳ {sim_days} Günlük Geleceği Simüle Et", use_container_width=True):
            if not api_key:
                st.error("⚠️ Sistem API Anahtarı eksik!")
            else:
                with st.spinner("Hesaplanıyor..."):
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
                            st.markdown(f'<div class="hastalik-alarm">🚨 KRİTİK ERKEN UYARI: {hastalik_adi} tehlikesi tespit etti!</div>', unsafe_allow_html=True)
                            st.markdown(sim_text[end_idx+1:].strip())
                        else:
                            st.success("✅ Otonom Kontrol: Risk tespit edilmedi.")
                            st.markdown(sim_text)
                    except Exception as e:
                        st.error(f"Hata: {e}")
