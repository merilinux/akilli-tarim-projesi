import streamlit as st
import plotly.graph_objects as go
import numpy as np
import cv2
import requests
from PIL import Image
from io import BytesIO
import time

st.set_page_config(layout="wide", page_title="BotaniX Ana Komuta Merkezi")

# ==========================================
# 1. ÜST PANEL: IOT SENSÖR VERİLERİ
# ==========================================
st.markdown("""
<div style="text-align:center; padding: 10px; margin-bottom: 20px;">
    <h1>🌍 BotaniX Otonom Çiftlik Komuta Merkezi</h1>
    <p style="font-size: 1.2rem; opacity: 0.8;">Tüm Filo, Arazi ve Yapay Zeka Verileri Tek Ekranda</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 📡 Tarladan Canlı IoT Telemetrisi")
col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡 Sıcaklık", "26.5 °C", "Normal")
col2.metric("💧 Hava Nemi", "%55", "-%2")
col3.metric("🌱 Toprak Nemi", "%60", "Sulama İstenmiyor")
col4.metric("🔋 Filo Bataryası", "%92", "İHA & İKA Hazır")
st.divider()

# ==========================================
# 2. ORTA PANEL: DİJİTAL İKİZ VE YAPAY ZEKA
# ==========================================
harita_sutunu, kamera_sutunu = st.columns([1.5, 1], gap="large")

with harita_sutunu:
    st.markdown("### 🗺️ Taktik Harita (Tüm Tarla)")
    harita_ekrani = st.empty()

with kamera_sutunu:
    st.markdown("### 🤖 FPV Kamera & Yapay Zeka")
    kamera_ekrani = st.empty()
    durum_paneli = st.empty()
    ai_sonuc_paneli = st.empty()

# Tarlanın Sabit Koordinatları (Konya) ve Rota
tarla_lon = [32.4840, 32.4850, 32.4850, 32.4840, 32.4840]
tarla_lat = [37.8710, 37.8710, 37.8720, 37.8720, 37.8710]
wp_lon = [32.4842, 32.4848, 32.4848, 32.4842]
wp_lat = [37.8712, 37.8712, 37.8718, 37.8718]

# Simülasyon Hafızası
if 'olgunluk_orani' not in st.session_state:
    st.session_state.olgunluk_orani = 0
if 'gorev_bitti' not in st.session_state:
    st.session_state.gorev_bitti = False

# ==========================================
# 3. ALT PANEL: AKSİYON VE OTONOMİ
# ==========================================
st.markdown("### 🚀 Otonom Filo Yönetimi")
if st.button("🛰️ İHA'yı Uçur ve Tarlayı Otonom Tara", type="primary", use_container_width=True):
    st.session_state.gorev_bitti = False
    
    # Çekilecek Örnek Fotoğraflar (Tarlanın farklı köşeleri)
    hedef_fotograflar = [
        "https://images.unsplash.com/photo-1596199050105-6d5d32222916?q=80&w=500", # Bol çilek
        "https://images.unsplash.com/photo-1518133501097-09d57a22f360?q=80&w=500", # Az çilek
        "https://images.unsplash.com/photo-1596199050105-6d5d32222916?q=80&w=500", # Bol çilek
        "https://images.unsplash.com/photo-1518133501097-09d57a22f360?q=80&w=500"  # Az çilek
    ]
    
    toplam_olgunluk = 0
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 🚁 DÖNGÜ: İHA HARİTADA GEZERKEN KAMERA GÖRÜNTÜ İŞLER
    for i in range(len(wp_lon)):
        # 1. HARİTAYI GÜNCELLE
        fig = go.Figure()
        fig.add_trace(go.Scattermapbox(lat=tarla_lat, lon=tarla_lon, mode='lines', fill='toself', name="Tarla Sınırı", marker=dict(color='cyan')))
        fig.add_trace(go.Scattermapbox(lat=wp_lat, lon=wp_lon, mode='lines', name="Otonom Rota", line=dict(color='yellow', dash='dot')))
        fig.add_trace(go.Scattermapbox(lat=[wp_lat[i]], lon=[wp_lon[i]], mode='markers+text', text=['🚁'], textfont=dict(size=35), name="İHA"))
        
        fig.update_layout(
            mapbox=dict(style="carto-darkmatter", center=dict(lat=37.8715, lon=32.4845), zoom=16.5),
            margin=dict(l=0, r=0, t=0, b=0), height=400, showlegend=False
        )
        harita_ekrani.plotly_chart(fig, use_container_width=True)
        
        # 2. KAMERAYI VE YAPAY ZEKAYI GÜNCELLE
        durum_paneli.warning(f"📍 Hedef {i+1} Noktası Taranıyor...")
        
        # İnternetten resmi çek
        response = requests.get(hedef_fotograflar[i], headers=headers)
        img_pil = Image.open(BytesIO(response.content))
        img_cv = np.array(img_pil)
        
        # OpenCV Kırmızı (Olgun) Tespiti
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2HSV)
        maske1 = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
        maske2 = cv2.inRange(hsv, np.array([160, 100, 100]), np.array([180, 255, 255]))
        tam_maske = maske1 + maske2
        sonuc = cv2.bitwise_and(img_cv, img_cv, mask=tam_maske)
        
        # Resmi sağ ekrana bas (Yapay zeka filtresiyle)
        kamera_ekrani.image(sonuc, caption=f"Hedef {i+1} Yapay Zeka Analizi", use_container_width=True)
        
        # Skoru hesapla
        kirmizi_piksel = cv2.countNonZero(tam_maske)
        oran = (kirmizi_piksel / (img_cv.shape[0] * img_cv.shape[1])) * 100 * 5
        toplam_olgunluk += oran
        ai_sonuc_paneli.info(f"Anlık Olgunluk Skoru: %{oran:.1f}")
        
        time.sleep(2) # Simülasyon hızı
        
    st.session_state.olgunluk_orani = toplam_olgunluk / len(wp_lon)
    st.session_state.gorev_bitti = True
    durum_paneli.success("✅ İHA Görevi Tamamladı! Üsse Dönülüyor.")

# ==========================================
# 4. FİNAL KARARI (İKA HASADI)
# ==========================================
if st.session_state.gorev_bitti:
    st.divider()
    st.markdown(f"### 🎯 Tarla Genel Hasat Raporu: **%{st.session_state.olgunluk_orani:.1f} Olgun**")
    
    if st.session_state.olgunluk_orani > 15.0:
        st.success("Tarlanın büyük bir kısmı hasada hazır!")
        if st.button("🚜 İKA'yı (Otonom Traktör) Hasada Gönder", type="primary", use_container_width=True):
            st.balloons()
            st.success("✅ İKA Garajdan Çıktı! Otonom hasat işlemi başlatıldı.")
            st.image("https://images.unsplash.com/photo-1628102491629-778571d893a3?q=80&w=1200", caption="İKA Canlı Operasyon Görüntüsü", use_container_width=True)
    else:
        st.warning("Tarladaki mahsul henüz tam olgunlaşmamış. İKA garajda bekletiliyor.")
