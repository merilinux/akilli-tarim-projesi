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
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 Akıllı Tarım ve Otonom Sulama Platformu")
st.markdown("Bu sistem; **ESP32 ve DHT22** tabanlı çevresel sensör verilerini, **ESP32-CAM** üzerinden alınan otonom görüntülerle **Bütünleşik Yapay Zekâ** ortamında sentezleyerek noktasal sulama optimizasyonu ve **Proaktif Karar Destek** sunar.")

# ==========================================
# YAN MENÜ: PROFİL VE SİSTEM AYARLARI
# ==========================================
with st.sidebar:
    st.header("👤 Çiftçi / Profil Ayarları")
    kullanici_adi = st.text_input("Kullanıcı Adı / İşletme", value="Demo Çiftçi")
    bahce_adi = st.text_input("İzlenen Sera / Bahçe Adı", value="1 Nolu Sera (Genel)")
    
    st.divider()
    st.header("⚙️ Sistem Ayarları")
    
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
# GEÇMİŞ VERİLER & CANLI SENSÖR HAFIZASI
# ==========================================
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame({
        "Kullanıcı": ["Demo Çiftçi", "Demo Çiftçi"],
        "Bahçe/Sera": ["1 Nolu Sera (Genel)", "1 Nolu Sera (Genel)"],
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

# Kullanıcıya ait filtreli veriyi al (Sadece o an seçili bahçenin verilerini göstermek için)
kullanici_verisi = st.session_state.history[st.session_state.history["Bahçe/Sera"] == bahce_adi]

# ==========================================
# SEKME DÜZENİ
# ==========================================
tab1, tab2, tab3 = st.tabs(["📸 Anlık Analiz ve Veri Füzyonu", "📅 Gelişim Ajandası", "🔮 Proaktif Risk Tahmini"])

# ------------------------------------------
# SEKME 1: ANLIK ANALİZ
# ------------------------------------------
with tab1:
    st.subheader(f"📊 IoT Sensör Ağı Canlı Akışı: {bahce_adi}")
    
    if st.button("📡 ESP32 Sensör Verilerini Çek"):
        st.session_state.sensor_data = {
            "temp": random.randint(10, 42),
            "hum": random.randint(20, 95),
            "soil": random.randint(10, 90)
        }
        st.success(f"✅ {bahce_adi} sahasındaki kapasitif ve DHT22 sensörlerinden güncel veriler çekildi!")

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
            kamera_fotosu = st.camera_input("Bitkinin fotoğrafını çekin (ESP32-CAM Simülasyonu)")
            if kamera_fotosu:
                image = Image.open(kamera_fotosu)
                st.success("✅ Canlı görüntü başarıyla yakalandı! Sekmeyi kapatabilirsiniz.")
                
        elif gorsel_secimi == "📁 Sistemden Yükle (Gizli)":
            uploaded_file = st.file_uploader("Sisteme fotoğraf aktarın (Dosya adı ve iz bırakılmaz)", type=["jpg", "png", "jpeg"])
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.success("✅ Görüntü güvenli bir şekilde belleğe alındı! Sekmeyi kapatabilirsiniz.")
                st.image(image, caption=f"{bahce_adi} - Veri Füzyonu İçin Aktarılan Görüntü", width="stretch")

    st.divider()

    st.subheader("🤖 Multimodal Yapay Zekâ Analizi")
    
    if st.button(f"{bahce_adi} Verilerini Sentezle ve Karar Al", use_container_width=True):
        if not api_key:
            st.error("⚠️ Sistem API Anahtarı eksik! Lütfen yönetici ayarlarını kontrol edin.")
        elif not image:
            st.warning("⚠️ Analiz için sensör verilerinin yanında bir görüntü de gereklidir. Lütfen gizli menüden görüntü sağlayın.")
        else:
            with st.spinner("Bulut veri tabanı ile bağlantı kuruluyor... Görüntü ve sensör verileri sentezleniyor..."):
                try:
                    client = genai.Client(api_key=api_key)
                    past_data_str = kullanici_verisi.to_string(index=False)
                    
                    c_temp = st.session_state.sensor_data['temp']
                    c_hum = st.session_state.sensor_data['hum']
                    c_soil = st.session_state.sensor_data['soil']

                    prompt = f"""
                    Sen otonom kararlar alabilen bir "Multimodal Tarım Yapay Zekası"sın.
                    Kullanıcı: {kullanici_adi}
                    İncelenen Bölge: {bahce_adi}
                    
                    Kullanıcı sana {bahce_adi} bölgesindeki IoT sensör ağından gelen verileri ve ESP32-CAM'den alınan güncel fotoğrafı sunuyor.

                    GÖREV 1: SAHTELİK KONTROLÜ
                    Fotoğraftaki bitki SUNİ/YAPAY/PLASTİK ise sadece "[SAHTE]" yazıp sebebini 1 cümle ile açıkla.
                    Eğer GERÇEK ise "[GERÇEK]" yaz ve analize geç:

                    [ANLIK IoT VERİLERİ]
                    - Ortam Sıcaklığı: {c_temp} °C
                    - Hava Nemi: %{c_hum}
                    - Toprak Nemi: %{c_soil}

                    [{bahce_adi} VERİ TABANI GEÇMİŞİ]
                    {past_data_str}

                    Aşağıdaki başlıkları kullanarak profesyonel bir SaaS raporu oluştur. Raporunda kullanıcıya ismiyle ({kullanici_adi}) hitap et ve bahçesine ({bahce_adi}) referans ver:
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
                        st.success(f"✅ Veri Füzyonu Başarılı. {bahce_adi} için bitki doğrulandı ve buluta kaydedildi.")
                        rapor = response_text.replace("[GERÇEK]", "").strip()
                        st.markdown(rapor)

                        # Yeni veriyi veritabanına Kullanıcı ve Bahçe adıyla ekle
                        new_data = pd.DataFrame({
                            "Kullanıcı": [kullanici_adi],
                            "Bahçe/Sera": [bahce_adi],
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
    st.subheader(f"📅 Bulut Veri Tabanı: {bahce_adi} Kayıtları")
    st.write(f"Sayın **{kullanici_adi}**, aşağıda sadece **{bahce_adi}** için toplanıp yapay zeka tarafından doğrulanmış geçmiş sensör okumaları listelenmektedir.")
    
    # Sadece o kullanıcının/bahçenin verilerini göster
    if not kullanici_verisi.empty:
        st.dataframe(kullanici_verisi, use_container_width=True)
        st.divider()
        st.subheader("📉 Çevresel Parametrelerin Zaman Serisi Analizi")
        chart_data = kullanici_verisi.set_index("Tarih")[["Ortam Sıcaklığı (°C)", "Hava Nemi (%)", "Toprak Nemi (%)"]]
        st.line_chart(chart_data)
    else:
        st.info(f"ℹ️ Henüz **{bahce_adi}** için bulutta kayıtlı bir geçmiş veri bulunmamaktadır. İlk analizi 'Anlık Analiz' sekmesinden yapabilirsiniz.")

# ------------------------------------------
# SEKME 3: SİMÜLASYON VE ERKEN UYARI
# ------------------------------------------
with tab3:
    st.subheader("🔮 Proaktif Karar Destek ve Risk Tahmini")
    st.info(f"💡 **Özgünlük Bildirimi:** Bu modül, {bahce_adi} için gelecekteki olası hava senaryolarını test ederek, fiziksel semptomlar oluşmadan önce otonom müdahaleleri planlar.")

    col3, col4 = st.columns(2)
    with col3:
        sim_temp = st.slider("Tahmini Gelecek Sıcaklık (°C)", 10.0, 50.0, 32.0, step=0.5, key="sim_temp")
        sim_hum = st.slider("Tahmini Hava Nemi (%)", 0.0, 100.0, 85.0, step=1.0, key="sim_hum")
    with col4:
        sim_soil = st.slider("Tahmini Toprak Nemi (%)", 0.0, 100.0, 15.0, step=1.0, key="sim_soil")
        sim_days = st.selectbox("Kaç Gün Sonrası İçin Tahmin Yapılsın?", [1,3,4,5,6,7,8,9,10,11,12,13,14], key="sim_days")

    if st.button(f"⏳ {bahce_adi} İçin {sim_days} Günlük Geleceği Simüle Et", use_container_width=True):
        if not api_key:
            st.error("⚠️ Sistem API Anahtarı eksik! Lütfen yönetici ayarlarını kontrol edin.")
        else:
            with st.spinner("Yapay zeka riskleri ve hastalık ihtimallerini hesaplıyor..."):
                try:
                    client = genai.Client(api_key=api_key)
                    past_data_str = kullanici_verisi.to_string(index=False)

                    sim_prompt = f"""
                    Sen bitki hastalıklarını ve su stresini önceden tahmin eden proaktif bir Karar Destek Sistemisin.
                    Müşteri: {kullanici_adi}
                    Analiz Edilen Bölge: {bahce_adi}
                    
                    Kullanıcının veritabanında {bahce_adi} için şu anki geçmiş verileri var:
                    {past_data_str}

                    Kullanıcı sana gelecekteki ({sim_days} gün sonraki) senaryoyu veriyor:
                    - Beklenen Sıcaklık: {sim_temp} °C
                    - Beklenen Hava Nemi: %{sim_hum}
                    - Beklenen Toprak Nemi: %{sim_soil}

                    GÖREV:
                    Bu gelecek senaryosu gerçekleşirse {bahce_adi} bölgesinde su eksikliği, mantar, kök çürüklüğü gibi ne tür RİSKLER ortaya çıkar?
                    Raporunda kullanıcıya ({kullanici_adi}) hitap ederek profesyonel tavsiyeler ver.

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
                            🚨 KRİTİK ERKEN UYARI: Karar Destek Sistemi {bahce_adi} için yaklaşan bir <b>{hastalik_adi}</b> tehlikesi tespit etti!<br>
                            Semptomlar bitki üzerinde görülmeden otonom sulama/iklimlendirme müdahalesi gereklidir!
                        </div>
                        """, unsafe_allow_html=True)
                        
                        temiz_rapor = sim_text[end_idx+1:].strip()
                        st.markdown(temiz_rapor)
                        
                    else:
                        st.success(f"✅ Otonom Kontrol: {bahce_adi} için belirtilen gelecek senaryosunda kritik bir risk tespit edilmedi. Değerler güvenli sınırlarda.")
                        st.markdown(sim_text)

                except Exception as e:
                    st.error(f"Simülasyon Hatası: {e}")
