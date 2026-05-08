import streamlit as st
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import time

st.markdown("""
<div style="text-align:center; padding: 10px; margin-bottom: 10px;">
    <h1>🌿 Botanix Otonom Filo</h1>
    <p style="font-size: 1rem; opacity: 0.8;">Taktik Harita ve FPV Kamera Merkezi</p>
</div>
""", unsafe_allow_html=True)

# Çekilen fotoğrafları hafızada tutmak için
if 'cekilen_fotograflar' not in st.session_state:
    st.session_state.cekilen_fotograflar = []

if 'drawn_coords' not in st.session_state:
    st.session_state.drawn_coords = None

st.markdown('<span class="section-label">📍 1. Adım: Tarlanı Uydu Üzerinde Çiz</span>', unsafe_allow_html=True)

KONYA_COORDS = [37.8715, 32.4846]
m = folium.Map(location=KONYA_COORDS, zoom_start=16)
folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Earth').add_to(m)

from folium.plugins import Draw
Draw(
    export=False, position='topleft',
    draw_options={'polyline': False, 'rectangle': False, 'circle': False, 'marker': False, 'circlemarker': False,
                  'polygon': {'showArea': True, 'metric': True, 'shapeOptions': {'color': 'cyan'}}}
).add_to(m)

output = st_folium(m, width=900, height=400, key="folium_map")

if output['last_active_drawing'] and output['last_active_drawing']['geometry']['type'] == 'Polygon':
    st.session_state.drawn_coords = output['last_active_drawing']['geometry']['coordinates'][0]

st.divider()

st.markdown('<span class="section-label">🎮 2. Adım: Otonom Uçuş ve Canlı Kamera İzleme</span>', unsafe_allow_html=True)

if st.session_state.drawn_coords and len(st.session_state.drawn_coords) > 3:
    poligon_koordinat = np.array(st.session_state.drawn_coords)
    min_lon, max_lon = poligon_koordinat[:, 0].min(), poligon_koordinat[:, 0].max()
    min_lat, max_lat = poligon_koordinat[:, 1].min(), poligon_koordinat[:, 1].max()

    # Rota Hesaplama
    wp_x, wp_y = [], []
    y_adimlar = np.linspace(min_lat, max_lat, 4) # Hızlı simülasyon için 4 satır
    yon = 1 
    for y in y_adimlar:
        satir_x = np.linspace(min_lon, max_lon, 4)
        if yon == -1: satir_x = np.flip(satir_x)
        for x in satir_x:
            wp_x.append(x)
            wp_y.append(y)
        yon *= -1

    # EKRANI İKİYE BÖLÜYORUZ (Sol: Harita, Sağ: Kamera)
    harita_alani, kamera_alani = st.columns([2, 1], gap="large")
    
    with harita_alani:
        st.markdown("**🗺️ Dijital İkiz (Taktik Harita)**")
        harita_gosterge = st.empty() # Animasyon için boş çerçeve

    with kamera_alani:
        st.markdown("**📸 İHA Sanal Kamera (FPV)**")
        kamera_gosterge = st.empty() # Kameranın fotoğraf basacağı boş çerçeve
        durum_metni = st.empty()

    if st.button("▶️ Uçuşu Başlat ve Görüntü Al", use_container_width=True):
        st.session_state.cekilen_fotograflar = [] # Yeni uçuşta hafızayı temizle
        
        # Temsili Tarla Görüntüleri (İnternetten)
        sanal_fotograflar = [
            "https://images.unsplash.com/photo-1592433054179-c5c2ab527e0a?w=500&q=80",
            "https://images.unsplash.com/photo-1530836369250-ef71a3f5e92d?w=500&q=80",
            "https://images.unsplash.com/photo-1628102491629-778571d893a3?w=500&q=80",
            "https://images.unsplash.com/photo-1586771107445-d3afbf0d1ddb?w=500&q=80"
        ]

        # PYTHON İLE ANİMASYON VE KAMERA DÖNGÜSÜ
        for i in range(len(wp_x)):
            # 1. Haritayı Güncelle
            fig = go.Figure()
            # Tarla Sınırı
            fig.add_trace(go.Scatter(x=poligon_koordinat[:, 0], y=poligon_koordinat[:, 1], mode='lines', fill='toself', line=dict(color='cyan', dash="dash"), name="Sınır"))
            # Rota
            fig.add_trace(go.Scatter(x=wp_x, y=wp_y, mode='lines', line=dict(color='yellow', dash='dot'), name='Rota'))
            # Drone'un O Anki Yeri
            fig.add_trace(go.Scatter(x=[wp_x[i]], y=[wp_y[i]], mode='text', text=['🚁'], textfont=dict(size=35), name='İHA'))
            
            fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=0, b=0), height=350, showlegend=False)
            harita_gosterge.plotly_chart(fig, use_container_width=True)

            # 2. Kamera Görüntüsünü Al ve Sağ Ekrana Bas
            durum_metni.warning(f"Hedef {i+1} taranıyor...")
            resim_url = sanal_fotograflar[i % len(sanal_fotograflar)] # 4 resmi sırayla dönsün
            
            # Görüntüyü kodun içine çekiyoruz (Deklanşör)
            response = requests.get(resim_url)
            cekilen_resim = Image.open(BytesIO(response.content))
            st.session_state.cekilen_fotograflar.append(cekilen_resim)
            
            # Sağ taraftaki ekrana basıyoruz
            kamera_gosterge.image(cekilen_resim, caption=f"📸 Hedef {i+1} Analiz Görüntüsü", use_container_width=True)
            
            time.sleep(1.5) # Drone 1.5 saniye sonra diğer noktaya geçsin

        durum_metni.success(f"✅ Uçuş Tamamlandı! {len(wp_x)} adet yüksek çözünürlüklü görüntü sisteme kaydedildi.")

else:
    st.info("ℹ️ Tarlayı parselledikten sonra otonom uçuş paneli açılacaktır.")
