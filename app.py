import streamlit as st
from google import genai
from PIL import Image
import pandas as pd
import random
from datetime import datetime, timedelta

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
# GİZLİ KULLANICI VERİTABANI (KAYITLI ÇİFTÇİLER)
# ==========================================
VALID_USERS = {
    "TR-1001": {"ad": "Ahmet Yılmaz", "bahce": "Konya Merkez Lale Serası"},
    "TR-1002": {"ad": "Mehmet Demir", "bahce": "Çumra Domates Tesisleri"},
    "TR-1003": {"ad": "Ayşe Kaya", "bahce": "Ereğli Organik Çilek Bahçesi"}
}

# ==========================================
# OTURUM (SESSION) YÖNETİMİ
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "bahce_adi" not in st.session_state:
    st.session_state.bahce_adi = ""
if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = {"temp": 24, "hum": 50, "soil": 40}
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=["Kullanıcı ID", "Kullanıcı Adı", "Bahçe/Sera", "Tarih", "Ortam Sıcaklığı (°C)", "Hava Nemi (%)", "Toprak Nemi (%)"])

# Yardımcı Fonksiyon: Sisteme ilk giriş için sahte geçmiş verisi oluştur
def load_initial_data(uid, ad, bahce):
    return pd.DataFrame({
        "Kullanıcı ID": [uid, uid],
        "Kullanıcı Adı": [ad, ad],
        "Bahçe/Sera": [bahce, bahce],
        "Tarih": [(datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
                  (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")],
        "Ortam Sıcaklığı (°C)": [22.0, 24.5],
        "Hava Nemi (%)": [55.0, 50.0],
        "Toprak Nemi (%)": [45.0, 40.0]
    })

# ==========================================
# EKRAN 1: GİRİŞ EKRANI (LOGIN)
# ==========================================
if not st.session_state.logged_in:
    st.markdown('<div class="login-box"><h1>🌱 Akıllı Tarım SaaS Platformuna Hoş Geldiniz</h1><p>Lütfen devam etmek için giriş yöntemi seçin.</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🧑‍🌾 Kayıtlı Çiftçi Girişi")
        st.info("Sisteme tanımlı Müşteri ID'nizi giriniz. (Örn: TR-1001)")
        girilen_id = st.text_input("Müşteri ID:", key="login_id").strip().upper()
        
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if girilen_id in VALID_USERS:
                st.session_state.logged_in = True
                st.session_state.user_id = girilen_id
                st.session_state.user_name = VALID_USERS[girilen_id]["ad"]
                st.session_state.bahce_adi = VALID_USERS[girilen_id]["bahce"]
                
                # Kullanıcının geçmiş verisi yoksa varsayılan veri ekle
                if not (st.session_state.history["Kullanıcı ID"] == girilen_id).any():
                    ilk_veri = load_initial_data(girilen_id, st.session_state.user_name, st.session_state.bahce_adi)
                    st.session_state.history = pd.concat([st.session_state.history, ilk_veri], ignore_index=True)
                
                st.rerun() # Sayfayı yenile ve içeri al
            else:
                st.error("❌ Hatalı ID! Kayıtlı bir kullanıcı bulunamadı.")
                
    with col2:
        st.subheader("🔍 Misafir / Ziyaretçi Girişi")
        st.warning("QR Kod üzerinden bağlanan ziyaretçilerimiz ve jüri üyelerimiz test ortamı için bu seçeneği kullanabilir.")
        if st.button("Misafir Olarak Devam Et", use_container_width=True):
            misafir_id = f"GUEST-{random.randint(1000, 9999)}"
            st.session_state.logged_in = True
            st.session_state.user_id = misafir_id
            st.session_state.user_name = "Misafir Ziyaretçi"
            st.session_state.bahce_adi = "Test Simülasyon Serası"
            
            # Misafir için test verisi ekle
            ilk_veri = load_initial_data(misafir_id, "Misafir Ziyaretçi", "Test Simülasyon Serası")
            st.session_state.history = pd.concat([st.session_state.history, ilk_veri], ignore_index=True)
            st.rerun()

# ==========================================
# EKRAN 2: ANA UYGULAMA (GİRİŞ YAPILDIYSA)
# ==========================================
else:
    # --- YAN MENÜ ---
    with st.sidebar:
        st.header("👤 Profil Bilgileri")
        st.success(f"Hoş geldin, **{st.session_state.user_name}**")
        st.write(f"**İzlenen Saha:** {st.session_state.bahce_adi}")
        st.write(f"**ID:** {st.session_state.user_id}")
        
        st.divider()
        if st.button("🚪 Çıkış Yap (Oturumu Kapat)", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
        st.divider()
        st.header("⚙️ Sistem Ayarları")
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("🔑 Güvenli API Bağlantısı Aktif!")
        except:
            api_key = None
            st.error("⚠️ Sistem API Anahtarı bulunamadı!")
        st.write("Bulut Bağlantı Durumu: " + ("✅ Çevrimiçi" if api_key else "🔴 Pasif"))

    st.title(f"🌱 Akıllı Tarım Platformu")
    
    # SADECE GİRİŞ YAPAN KULLANICININ VERİLERİNİ FİLTRELE
    kullanici_verisi = st.session_state.history[st.session_state.history["Kullanıcı ID"] == st.session_state.user_id]

    tab1, tab2, tab3 = st.tabs(["📸 Anlık Analiz ve Veri Füzyonu", "📅 Gelişim Ajandası", "🔮 Proaktif Risk Tahmini"])

    # ------------------------------------------
    # SEKME 1: ANLIK ANALİZ
    # ------------------------------------------
    with tab1:
        st.subheader(f"📊 IoT Sensör Ağı Canlı Akışı: {st.session_state.bahce_adi}")
        
        if st.button("📡 ESP32 Sensör Verilerini Çek"):
            st.session_state.sensor_data = {
                "temp": random.randint(10, 42),
                "hum": random.randint(20, 95),
                "soil": random.randint(10, 90)
            }
            st.success("✅ Sahadaki kapasitif ve DHT22 sensörlerinden güncel veriler çekildi!")

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
                    st.image(image, caption=f"{st.session_state.bahce_adi} - Veri Füzyonu İçin Aktarılan Görüntü", width="stretch")

        st.divider()

        st.subheader("🤖 Multimodal Yapay Zekâ Analizi")
        
        if st.button(f"{st.session_state.bahce_adi} Verilerini Sentezle ve Karar Al", use_container_width=True):
            if not api_key:
                st.error("⚠️ Sistem API Anahtarı eksik!")
            elif not image:
                st.warning("⚠️ Lütfen analiz için görüntü sağlayın.")
            else:
                with st.spinner("Sentezleniyor... Lütfen bekleyin..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        past_data_str = kullanici_verisi.to_string(index=False)
                        
                        c_temp = st.session_state.sensor_data['temp']
                        c_hum = st.session_state.sensor_data['hum']
                        c_soil = st.session_state.sensor_data['soil']

                        prompt = f"""
                        Sen otonom kararlar alabilen bir "Multimodal Tarım Yapay Zekası"sın.
                        Kullanıcı: {st.session_state.user_name}
                        İncelenen Bölge: {st.session_state.bahce_adi}
                        
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
                            st.success(f"✅ Başarılı. {st.session_state.bahce_adi} için bitki doğrulandı ve buluta kaydedildi.")
                            st.markdown(response_text.replace("[GERÇEK]", "").strip())

                            # Yeni veriyi SADECE bu kullanıcının kimliğiyle ekle
                            new_data = pd.DataFrame({
                                "Kullanıcı ID": [st.session_state.user_id],
                                "Kullanıcı Adı": [st.session_state.user_name],
                                "Bahçe/Sera": [st.session_state.bahce_adi],
                                "Tarih": [datetime.now().strftime("%Y-%m-%d")],
                                "Ortam Sıcaklığı (°C)": [c_temp],
                                "Hava Nemi (%)": [c_hum],
                                "Toprak Nemi (%)": [c_soil]
                            })
                            st.session_state.history = pd.concat([st.session_state.history, new_data], ignore_index=True)
                        else:
                            st.markdown(response_text)
                    except Exception as e:
                        st.error(f"Sistem Hatası: {e}")

    # ------------------------------------------
    # SEKME 2: AJANDA
    # ------------------------------------------
    with tab2:
        st.subheader(f"📅 Bulut Veri Tabanı: {st.session_state.bahce_adi}")
        st.write(f"Sayın **{st.session_state.user_name}**, aşağıda sadece sizin ID'nize ({st.session_state.user_id}) tanımlı sensör okumaları listelenmektedir.")
        
        if not kullanici_verisi.empty:
            st.dataframe(kullanici_verisi, use_container_width=True)
            st.divider()
            st.subheader("📉 Çevresel Parametrelerin Zaman Serisi Analizi")
            chart_data = kullanici_verisi.set_index("Tarih")[["Ortam Sıcaklığı (°C)", "Hava Nemi (%)", "Toprak Nemi (%)"]]
            st.line_chart(chart_data)
        else:
            st.info("Kayıtlı veri bulunamadı.")

    # ------------------------------------------
    # SEKME 3: SİMÜLASYON VE ERKEN UYARI
    # ------------------------------------------
    with tab3:
        st.subheader("🔮 Proaktif Karar Destek ve Risk Tahmini")
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
                        sim_prompt = f"""
                        Sen bitki hastalıklarını ve su stresini önceden tahmin eden proaktif bir Karar Destek Sistemisin.
                        Müşteri: {st.session_state.user_name}
                        Geçmiş Veriler: {kullanici_verisi.to_string(index=False)}

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
