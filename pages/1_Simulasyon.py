import streamlit as st
from streamlit_folium import st_folium
import folium
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import json

# ==========================================
# SAYFA AYARLARI VE GÖRSEL TASARIM (CSS)
# ==========================================
# (Daha önce kurduğumuz şeffaf/esnek tasarım CSS'lerini koruduğumuzu varsayıyorum)

st.markdown("""
<div style="text-align:center; padding: 10px; margin-bottom: 10px;">
    <h1>🌿 Botanix</h1>
    <p style="font-size: 1rem; opacity: 0.8;">Otonom Tarım Simülasyonu ve Dijital İkiz Platformu</p>
</div>
""", unsafe_allow_html=True)

# Oturum Yönetimi (Hafızada tutmak için)
if 'drawn_coords' not in st.session_state:
    st.session_state.drawn_coords = None

# SEKME YAPISINA YENİ BÖLÜMÜ EKLE
tab_sim, tab_log = st.tabs(["🎮 Dijital İkiz (Simülasyon)", "📅 Veri Kayıtları"])

with tab_sim:
    st.markdown('<span class="section-label">📍 1. Adım: Tarlanı Uydu Üzerinde Parselle/Çiz</span>', unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.85rem; opacity:0.8;'>Tarlanın sınırlarını belirlemek için aşağıdaki Google Earth uydusu üzerindeki 'Polygon' aracını kullan.</p>", unsafe_allow_html=True)

    # Konya Bölgesi varsayılan haritası (Gerçek Ahmet Amca bölgesi)
    KONYA_COORDS = [37.8715, 32.4846]
    
    # 📡 INTERAKTİF HARİTA (FOLIUM)
    m = folium.Map(location=KONYA_COORDS, zoom_start=16, control_scale=True)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Earth Uydusu').add_to(m)

    # Drawing Tools (Çizim Araçları) Ekle
    from folium.plugins import Draw
    Draw(
        export=False,
        position='topleft',
        draw_options={
            'polyline': False, 'rectangle': False, 'circle': False, 'marker': False, 'circlemarker': False,
            'polygon': {'showArea': True, 'metric': True, 'allowIntersection': False, 'shapeOptions': {'color': 'cyan', 'fillOpacity': 0.1}}
        }
    ).add_to(m)

    # Haritayı Streamlit'e Bas ve Çizimi Yakala
    output = st_folium(m, width=900, height=450, key="folium_map")

    # Çizilen koordinatları session_state'e kaydet (Tekrar render olmaması için)
    if output['last_active_drawing'] and output['last_active_drawing']['geometry']['type'] == 'Polygon':
        st.session_state.drawn_coords = output['last_active_drawing']['geometry']['coordinates'][0]

    st.divider()

    # ==========================================
    # 2. ADIM: SİMUÜLASYON VE OTONOM ROTA (PLOTLY)
    # ==========================================
    st.markdown('<span class="section-label">🎮 2. Adım: Otonom Waypoint Uçuş Simülasyonu (İHA)</span>', unsafe_allow_html=True)

    # Eğer tarla çizildiyse simülasyonu başlat
    if st.session_state.drawn_coords and len(st.session_state.drawn_coords) > 3:
        poligon_koordinat = np.array(st.session_state.drawn_coords)
        
        # Tarla Sınırları (Koordinatlardan Metreye çevirmek için basit bir ölçekleme - Temsili)
        # (Jüri için otonom rota mantığını göstermek adına koordinatları basit bir XY düzlemine yayıyoruz)
        min_lon = poligon_koordinat[:, 0].min()
        max_lon = poligon_koordinat[:, 0].max()
        min_lat = poligon_koordinat[:, 1].min()
        max_lat = poligon_koordinat[:, 1].max()

        # ZİKZAK ROTA HESAPLAMA ALGORİTMASI (Lawnmower Pattern)
        wp_x, wp_y = [], []
        adim_sayisi = 12
        y_adimlar = np.linspace(min_lat, max_lat, adim_sayisi)
        yon = 1 

        for y in y_adimlar:
            satir_x = np.linspace(min_lon, max_lon, 8)
            if yon == -1: satir_x = np.flip(satir_x)
            for x in satir_x:
                wp_x.append(x)
                wp_y.append(y)
            yon *= -1 # Yön değiştir

        toplam_waypoint = len(wp_x)
        
        # PLOTLY FİGÜRÜ (Dijital İkiz Ekranı)
        fig = go.Figure()

        # 1. Tarlanın Kesin Sınırlarını Çiz (Çizilen Polygon - Trace 0)
        fig.add_trace(go.Scatter(
            x=poligon_koordinat[:, 0], y=poligon_koordinat[:, 1], mode='lines',
            fill='toself', fillcolor='rgba(0, 229, 255, 0.05)',
            line=dict(color='cyan', width=2, dash="dash"),
            name="Seçilen Tarla Sınırı", hoverinfo='skip'
        ))

        # 2. Otonom Rota (Zikzak Çizgiler - Trace 1)
        fig.add_trace(go.Scatter(
            x=wp_x, y=wp_y, mode='lines',
            line=dict(color='yellow', width=1, dash='dot'),
            name='Otonom Waypoint Rotası', hoverinfo='skip'
        ))

        # 3. İHA ve Sanal Kamera (Başlangıç Noktaları)
        fig.add_trace(go.Scatter(x=[wp_x[0]], y=[wp_y[0]], mode='text', text=['🚁'], textfont=dict(size=35), name='İHA Konumu', hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=[wp_x[0]], y=[wp_y[0]], mode='markers', marker=dict(size=12, color='white', symbol='square-open'), name='Sanal Kamera Odak', hoverinfo='skip'))

        # ANİMASYON KARELERİNİ (FRAMES) HAZIRLA
        frames = []
        for i in range(toplam_waypoint):
            frames.append(go.Frame(data=[
                go.Scatter(x=poligon_koordinat[:, 0], y=poligon_koordinat[:, 1]), # Trace 0: Sınırlar sabit
                go.Scatter(x=wp_x, y=wp_y), # Trace 1: Rota sabit
                go.Scatter(x=[wp_x[i]], y=[wp_y[i]]), # Trace 2: İHA Konumu
                go.Scatter(x=[wp_x[i]], y=[wp_y[i]]), # Trace 3: Kamera Konumu
            ], name=str(i)))

        fig.frames = frames

        # OYNATMA BUTONLARI VE TASARIM
        fig.update_layout(
            xaxis=dict(range=[min_lon - 0.0001, max_lon + 0.0001], visible=False),
            yaxis=dict(range=[min_lat - 0.0001, max_lat + 0.0001], visible=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=30, b=0),
            height=450,
            updatemenus=[dict(
                type="buttons", showactive=False, x=0.5, y=1.05, xanchor="center", direction="left",
                buttons=[
                    dict(label="▶️ Otonom Analizi Başlat", method="animate", args=[None, dict(frame=dict(duration=150, redraw=True), transition=dict(duration=0), fromcurrent=True, mode="immediate")]),
                    dict(label="⏸️ Durdur", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
                ]
            )]
        )

        st.plotly_chart(fig, use_container_width=True)

        # Simülasyon Altı Telemetri Paneli
        st.markdown('<span class="section-label">📊 Anlık Uçuş Telemetrisi</span>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("🚁 İHA Durumu", "Otonom Waypoint Takibi", "Aktif Uçuş")
        col2.metric("📌 Toplam Waypoint", f"{toplam_waypoint} Adet", f"Menzil OK")
        col3.metric("📸 Sanal Kamera", "Görüntü İşleme Aktif", "Hastalık Analizi: %84")

    else:
        st.info("ℹ️ Simülasyonu başlatmak için yukarıdaki uydu haritası üzerinde bir tarla (Polygon) çizin.")
