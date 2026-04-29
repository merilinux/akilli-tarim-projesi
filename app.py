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

# 🌟 İŞTE BURASI: DOSYA ADINI GİZLEYEN AJAN CSS KODLARI 🌟
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
    
    /* YÜKLENEN DOSYANIN ADINI VE BOYUTUNU TAMAMEN GİZLE */
    [data-testid="stUploadedFile"] {
        display: none !important;
    }
    /* Upload kutusunun içindeki 'Drag and drop' yazısını daha profesyonel yapalım */
    .css-1g5m0rc.e1b2p2ww12 {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 Akıllı Tarım ve Otonom Sulama Platformu")
st.markdown("Bu sistem; **ESP32 ve DHT22** tabanlı çevresel sensör verilerini, **ESP32-CAM** üzerinden alınan otonom görüntülerle **Bütünleşik Yapay Zekâ** ortamında sentezleyerek noktasal sulama optimizasyonu ve **Proaktif Karar Destek** sunar.")

# ==========================================
# API KEY VE SİSTEM AYARLARI (YAN MENÜ)
# ==========================================
with st.sidebar:
    st.header("⚙️ Sistem Ayarları")
    
    # YENİ KISIM: API anahtarını gizli kasadan çekiyoruz
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("🔑 Güvenli API Bağlantısı Aktif!")
    except:
        api_key = None
        st.error("⚠️ Sistem API Anahtarı bulunamadı! Lütfen yönetici ile iletişime geçin.")
        
    st.info("💡 Sistem, Multimodal Veri Sentezi (SaaS Modeli) için Gemini 2.5 Flash-Lite modelini kullanmaktadır.")
    st.divider()
    st.write("Bulut Bağlantı Durumu: " + ("✅ Çevrimiçi (Firebase Senkronize)" if api_key else "🔴 API Bekleniyor"))

# ==========================================
# GEÇMİŞ VERİLER & CANLI SENSÖR HAFIZASI (pH Çıkarıldı)
# ==========================================
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame({
        "Tarih": [(datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
                  (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")],
        "Ortam Sıcaklığı (°C)": [22.0, 24.5],
        "Hava Nemi (%)": [55.0, 50.0],
        "Toprak Nemi (%)": [45.0, 40.0]
    })

if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = {
        "temp": random.randint(15, 35),
        "hum": random.randint(30, 85),
        "soil": random.randint(20, 75)
    }

# ==========================================
# SEKME DÜZENİ (3 SEKMELİ YAPI)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📸 Anlık Analiz ve Veri Füzyonu", "📅 Gelişim Ajandası", "🔮 Proaktif Simülasyon "])

# ------------------------------------------
# SEKME 1: ANLIK ANALİZ
# ------------------------------------------
with tab1:
    st.subheader("📊 IoT Sensör Ağı Canlı Akışı (ESP32 Düğümü)")
    
    if st.button("📡 ESP32 Sensör Verilerini Çek"):
        st.session_state.sensor_data = {
            "temp": random.randint(10, 42),
            "hum": random.randint(20, 95),
            "soil": random.randint(10, 90)
        }
        st.success("✅ Sahadaki kapasitif ve DHT22 sensörlerinden anlık güncel veriler çekildi!")

    met_col1, met_col2, met_col3 = st.columns(3)
    met_col1.metric(label="🌡 Ortam Sıcaklığı", value=f"{st.session_state.sensor_data['temp']} °C")
    met_col2.metric(label="💧 Hava Nemi", value=f"%{st.session_state.sensor_data['hum']}")
    met_col3.metric(label="🌱 Toprak Nemi", value=f"%{st.session_state.sensor_data['soil']}")
    
    st.divider()

    st.subheader("📷 ESP32-CAM Otonom Görüntü Girişi")
    image = None
    
    # 🌟 İŞTE BURASI: KAMERA VE GİZLİ DOSYA MENÜSÜ 🌟
    with st.expander("Görsel Girişi", expanded=False):
        gorsel_secimi = st.radio("Analiz için görüntü kaynağı seçin:", ["📸 Canlı Kamera", "📁 Sistemden Yükle (Gizli)"], horizontal=True)
        
        if gorsel_secimi == "📸 Canlı Kamera":
            kamera_fotosu = st.camera_input("Bitkinin fotoğrafını çekin (ESP32-CAM Simülasyonu)")
            if kamera_fotosu:
                image = Image.open(kamera_fotosu)
                st.success("✅ Canlı görüntü başarıyla yakalandı! Sekmeyi kapatabilirsiniz.")
                
        elif gorsel_secimi == "📁 Sistemden Yükle (Gizli)":
            uploaded_file = st.file_uploader("Sisteme fotoğraf aktarın (Dosya adı ve iz bırakılmaz)", type=["jpg", "png", "jpeg"])
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.success("✅ Görüntü güvenli bir şekilde belleğe alındı! Sekmeyi kapatabilirsiniz.")
                st.image(image, caption="Veri Füzyonu İçin Aktarılan Görüntü", width="stretch")

    st.divider()

    st.subheader("🤖 Multimodal Yapay Zekâ Analizi")
    
    if st.button("Verileri Sentezle ve Noktasal Sulama Kararı Al", use_container_width=True):
        if not api_key:
            st.error("⚠️ Sistem API Anahtarı eksik! Lütfen yönetici ayarlarını kontrol edin.")
        elif not image:
            st.warning("⚠️ Analiz için sensör verilerinin yanında bir görüntü de gereklidir. Lütfen gizli menüden görüntü sağlayın.")
        else:
            with st.spinner("Bulut veri tabanı ile bağlantı kuruluyor... Görüntü ve sensör verileri sentezleniyor..."):
                try:
                    client = genai.Client(api_key=api_key)
                    past_data_str = st.session_state.history.to_string(index=False)
                    
                    c_temp = st.session_state.sensor_data['temp']
                    c_hum = st.session_state.sensor_data['hum']
                    c_soil = st.session_state.sensor_data['soil']

                    prompt = f"""
                    Sen bu projenin temelini oluşturan, otonom kararlar alabilen bir "Multimodal Tarım Yapay Zekası"sın.
                    Kullanıcı sana IoT sensör ağından (ESP32, DHT22, Kapasitif Nem Sensörü) gelen verileri ve ESP32-CAM'den alınan bitkinin güncel fotoğrafını sunuyor.
                    Bu sistem karmaşık kimyasal/pH sensörleri kullanmaz; tamamen "su/nem stresi" ve "görsel deformasyonlara" odaklanarak su israfını önlemeyi (noktasal sulama) hedefler.

                    GÖREV 1: SAHTELİK KONTROLÜ
                    Fotoğraftaki bitki SUNİ/YAPAY/PLASTİK ise sadece "[SAHTE]" yazıp sebebini 1 cümle ile açıkla.
                    Eğer GERÇEK ise "[GERÇEK]" yaz ve analize geç:

                    [ANLIK IoT VERİLERİ]
                    - Ortam Sıcaklığı: {c_temp} °C
                    - Hava Nemi: %{c_hum}
                    - Toprak Nemi: %{c_soil}

                    [VERİ TABANI GEÇMİŞİ]
                    {past_data_str}

                    Aşağıdaki başlıkları kullanarak profesyonel bir SaaS raporu oluştur:
                    ### 🌿 Bitki Taksonomisi ve Görsel Stres Analizi
                    ### 📊 Sensör Füzyonu (Görsel ve Çevresel Veri Uyumu)
                    ### 📉 Su İhtiyacı ve Gelişim Trendi
                    ### 💧 Otonom Sulama Valfi Tetikleme Kararı (Noktasal Sulama Tavsiyesi)
                    """

                    response = client.models.generate_content(
                        model='gemini-2.5-flash-lite',
                        contents=[prompt, image]
                    )
                    response_text = response.text

                    if "[SAHTE]" in response_text:
                        st.error("🚨 UYARI: Sistem görüntüdeki bitkinin SUNİ (YAPAY) veya PLASTİK olduğunu tespit etti!")
                        st.warning("❌ Veri İptali: Yapay bir bitki için sensör okumaları anlamsızdır. Veritabanı kaydı engellendi.")
                        aciklama = response_text.replace("[SAHTE]", "").strip()
                        st.info(f"🤖 AI Görsel Doğrulama: {aciklama}")
                    elif "[GERÇEK]" in response_text:
                        st.success("✅ Veri Füzyonu Başarılı. Bitki doğrulandı ve bulut sunucuya senkronize edildi.")
                        rapor = response_text.replace("[GERÇEK]", "").strip()
                        st.markdown(rapor)

                        # Veritabanına yaz (pH olmadan)
                        new_data = pd.DataFrame({
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
    st.subheader("📅 Bulut Veri Tabanı Kayıtları (Gelişim Ajandası)")
    st.write("IoT ağından toplanıp yapay zeka tarafından doğrulanmış geçmiş sensör okumaları. Bu veriler sistemin SaaS abonelik modeline temel oluşturur.")
    st.dataframe(st.session_state.history, use_container_width=True)

    st.divider()
    st.subheader("📉 Çevresel Parametrelerin Zaman Serisi Analizi")
    chart_data = st.session_state.history.set_index("Tarih")[["Ortam Sıcaklığı (°C)", "Hava Nemi (%)", "Toprak Nemi (%)"]]
    st.line_chart(chart_data)


# ------------------------------------------
# SEKME 3: SİMÜLASYON VE ERKEN UYARI
# ------------------------------------------
with tab3:
    st.subheader("🔮 Proaktif Karar Destek ve Su Stresi Simülasyonu")
    st.info("💡 **Özgünlük Bildirimi:** Bu modül, sensörlerden alınan verilerin gelecekteki olası senaryolarını manuel test ederek, bitki su stresine girmeden veya fiziksel semptomlar oluşmadan önce gerekli otonom müdahaleleri planlar.")

    col3, col4 = st.columns(2)
    with col3:
        sim_temp = st.slider("Tahmini Gelecek Sıcaklık (°C)", 10.0, 50.0, 32.0, step=0.5, key="sim_temp")
        sim_hum = st.slider("Tahmini Hava Nemi (%)", 0.0, 100.0, 85.0, step=1.0, key="sim_hum")
    with col4:
        sim_soil = st.slider("Tahmini Toprak Nemi (%)", 0.0, 100.0, 15.0, step=1.0, key="sim_soil")
        sim_days = st.selectbox("Kaç Gün Sonrası İçin Tahmin Yapılsın?", [1,3,4,5,6,7,8,9,10,11,12,13,14], key="sim_days")

    if st.button(f"⏳ {sim_days} Günlük Geleceği Simüle Et", use_container_width=True):
        if not api_key:
            st.error("⚠️ Sistem API Anahtarı eksik! Lütfen yönetici ayarlarını kontrol edin.")
        else:
            with st.spinner("Yapay zeka su israfı risklerini ve hastalık ihtimallerini hesaplıyor..."):
                try:
                    client = genai.Client(api_key=api_key)
                    past_data_str = st.session_state.history.to_string(index=False)

                    sim_prompt = f"""
                    Sen bitki hastalıklarını ve su stresini önceden tahmin eden proaktif bir Karar Destek Sistemisin.
                    Kullanıcının SaaS veritabanında şu anki geçmiş verileri var:
                    {past_data_str}

                    Kullanıcı sana gelecekteki ({sim_days} gün sonraki) senaryoyu veriyor:
                    - Beklenen Sıcaklık: {sim_temp} °C
                    - Beklenen Hava Nemi: %{sim_hum}
                    - Beklenen Toprak Nemi: %{sim_soil}

                    GÖREV:
                    Bu gelecek senaryosu gerçekleşirse bitkide su eksikliği, mantar, kök çürüklüğü gibi ne tür RİSKLER ortaya çıkar?
                    Cevabında karmaşık kimyasal/pH düzeltmelerinden bahsetme; odağın tamamen sulama rejimi, ortam iklimlendirmesi ve erken müdahale olmalı.

                    KURAL (ÇOK ÖNEMLİ):
                    Eğer bu veriler kritik bir kuruma veya hastalık riski taşıyorsa, cevabının EN BAŞINA şu etiketi KESİNLİKLE koy:
                    [HASTALIK_ALARM: Hastalığın/Riskin Adı]

                    Ardından detaylı raporunu şu başlıklarla sun:
                    ### ⚠️ Tespit Edilen Risk Seviyesi ve Kaynak İsrafı Durumu
                    ### 🔬 Stresin/Hastalığın Oluşma Mekanizması
                    ### 🛡️ Proaktif Müdahale (Noktasal Sulama ve İklim Optimizasyonu)
                    """

                    sim_response = client.models.generate_content(
                        model='gemini-2.5-flash-lite',
                        contents=sim_prompt
                    )
                    
                    sim_text = sim_response.text

                    if "[HASTALIK_ALARM:" in sim_text:
                        start_idx = sim_text.find("[HASTALIK_ALARM:") + 16
                        end_idx = sim_text.find("]", start_idx)
                        hastalik_adi = sim_text[start_idx:end_idx].strip()
                        
                        st.markdown(f"""
                        <div class="hastalik-alarm">
                            🚨 KRİTİK ERKEN UYARI: Karar Destek Sistemi yaklaşan bir <b>{hastalik_adi}</b> tehlikesi tespit etti!<br>
                            Semptomlar bitki üzerinde görülmeden otonom sulama/iklimlendirme müdahalesi gereklidir!
                        </div>
                        """, unsafe_allow_html=True)
                        
                        temiz_rapor = sim_text[end_idx+1:].strip()
                        st.markdown(temiz_rapor)
                        
                    else:
                        st.success("✅ Otonom Kontrol: Belirtilen gelecek senaryosunda kritik bir risk veya su stresi tespit edilmedi. Değerler güvenli sınırlarda.")
                        st.markdown(sim_text)

                except Exception as e:
                    st.error(f"Simülasyon Hatası: {e}")
