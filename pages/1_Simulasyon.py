import streamlit as st
import cv2
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import time

st.set_page_config(layout="wide")

st.markdown("""
<div style="text-align:center; padding: 10px; margin-bottom: 20px;">
    <h1>🍓 BotaniX Akıllı Çiftlik Yönetimi</h1>
    <p style="font-size: 1.2rem; opacity: 0.8;">Ahmet Amca'nın Evdeki Tablet Ekranı (Otonom Karar Destek Sistemi)</p>
</div>
""", unsafe_allow_html=True)

# Sensör Verileri (IoT bağlantını temsil eder)
st.markdown("### 📡 Tarladan Gelen Anlık Sensör Verileri")
col_t, col_h, col_s = st.columns(3)
col_t.metric("🌡 Hava Sıcaklığı", "26.5 °C", "Uygun")
col_h.metric("💧 Hava Nemi", "%55", "-%2")
col_s.metric("🌱 Toprak Nemi", "%60", "Sulama Gerekmiyor")

st.divider()

# Sistem Durumu Hafızası
if 'iha_uctu_mu' not in st.session_state:
    st.session_state.iha_uctu_mu = False
if 'olgunluk_orani' not in st.session_state:
    st.session_state.olgunluk_orani = 0

st.markdown("### 🚁 1. Aşama: Otonom Keşif ve Görüntü İşleme")

if st.button("🛰️ Drone'u (İHA) Tarlaya Gönder ve Çilekleri Kontrol Et", use_container_width=True):
    st.session_state.iha_uctu_mu = True
    
    with st.spinner('Drone tarlaya uçuyor ve görüntü alıyor...'):
        time.sleep(2) # Drone uçuş süresi simülasyonu
        
        # Çilek Tarlası Görüntüsü Çekme (Bot Korumasını Aşarak)
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://images.unsplash.com/photo-1596199050105-6d5d32222916?q=80&w=800&auto=format&fit=crop" # Çilek resmi
        response = requests.get(url, headers=headers)
        img_pil = Image.open(BytesIO(response.content))
        img_cv = np.array(img_pil)
        
        # Ekranı İkiye Böl: Sol Ham Görüntü, Sağ Yapay Zeka
        kamera_col, ai_col = st.columns(2)
        
        with kamera_col:
            st.image(img_pil, caption="📸 Drone'dan Gelen Canlı Görüntü (RGB)", use_container_width=True)
            
        with ai_col:
            # OPENCV İLE OLGUN (KIRMIZI) ÇİLEK TESPİTİ
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2HSV)
            
            # Kırmızı renk HSV'de iki bölgededir, ikisini de alıyoruz
            alt_kirmizi1 = np.array([0, 100, 100])
            ust_kirmizi1 = np.array([10, 255, 255])
            maske1 = cv2.inRange(hsv, alt_kirmizi1, ust_kirmizi1)
            
            alt_kirmizi2 = np.array([160, 100, 100])
            ust_kirmizi2 = np.array([180, 255, 255])
            maske2 = cv2.inRange(hsv, alt_kirmizi2, ust_kirmizi2)
            
            tam_maske = maske1 + maske2
            
            # Maskeyi resme uygula (Sadece kırmızı çilekler parlasın)
            sonuc = cv2.bitwise_and(img_cv, img_cv, mask=tam_maske)
            
            st.image(sonuc, caption="🧠 Yapay Zeka Filtresi (Sadece Olgun Çilekler Algılandı)", use_container_width=True)
            
            # Piksellerden hasat oranını hesapla
            kirmizi_piksel = cv2.countNonZero(tam_maske)
            toplam_piksel = img_cv.shape[0] * img_cv.shape[1]
            st.session_state.olgunluk_orani = (kirmizi_piksel / toplam_piksel) * 100 * 5 # Oranı görselleştirmek için çarpan

if st.session_state.iha_uctu_mu:
    st.info(f"📊 **Yapay Zeka Analiz Raporu:** Tarladaki çileklerin **%{st.session_state.olgunluk_orani:.1f}'i** hasada hazır (kızarmış) durumda.")
    
    st.markdown("### 🚜 2. Aşama: Otonom Hasat Kararı")
    
    # EĞER ÇİLEKLER OLGUNSA İKA BUTONU AÇILSIN
    if st.session_state.olgunluk_orani > 15.0: # Yüzde 15'ten fazlası kızarmışsa
        st.success("✅ Hasat eşiği geçildi. Tarladaki mahsul olgunlaşmış!")
        
        if st.button("🤖 Otonom Hasat Robotunu (İKA) Göreve Çıkar", type="primary", use_container_width=True):
            with st.spinner('İKA Garajdan Çıkıyor... Hedef Koordinata Gidiliyor...'):
                time.sleep(3)
                
            st.balloons()
            st.success("🚜 İKA başarıyla tarlaya ulaştı ve otonom hasat işlemine başladı. Ahmet Amca, kahvenizi yudumlamaya devam edebilirsiniz!")
            
            # Hasat animasyonu / gif eklenebilir
            st.image("https://images.unsplash.com/photo-1628102491629-778571d893a3?q=80&w=800", caption="İKA Tarlada Hasat Yapıyor (Canlı Bağlantı)", width=400)
    else:
        st.warning("⏳ Mahsul henüz yeterince olgunlaşmamış. Hasat robotu (İKA) beklemede kalacak.")
