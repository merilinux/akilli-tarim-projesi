# ------------------------------------------
    # SEKME 4: DRONE UÇUŞ PLANLAYICI (FAZ-2) - KUSURSUZ ENTEGRASYON
    # ------------------------------------------
    with tab4:
        st.markdown('<span class="section-label">🚁 Otonom Drone Uçuş Planlayıcı (Uydu Haritası)</span>', unsafe_allow_html=True)
        st.markdown("""
        <p style='font-size:0.9rem; opacity:0.8;'>
        Algoritma, otonom uçuş sırasında kameranın (mavi kutunun) tarlanın dışına taşmasını engellemek için drone'un rotasını (sarı çizgi) güvenli bir iç çembere hapseder. 
        Kamera ayak izi, tarlanın sınırlarına milimetrik olarak teğet geçer.
        </p>
        """, unsafe_allow_html=True)

        SENIN_GITHUB_RESIM_LINKIN = "https://raw.githubusercontent.com/merilinux/akilli-tarim-projesi/main/Gemini_Generated_Image_uvl9gtuvl9gtuvl9.png"
        
        # 🔥 İŞTE BENİM SİLDİĞİM VE SİSTEMİ ÇÖKERTEN O SATIRI GERİ EKLEDİM! 🔥
        GITHUB_GELISTIRME_MODE = True 

        # GÖRSELDEKİ KOYU YEŞİL TARLAYA GÖRE PİKSEL PİKSEL HESAPLANMIŞ VARSAYILANLAR
        with st.expander("📍 Tarla Sınırlarını Belirle (Poligon Koordinatları)", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                x1 = st.number_input("Sol Alt X", value=320)
                y1 = st.number_input("Sol Alt Y", value=170)
            with c2:
                x2 = st.number_input("Sağ Alt X", value=800)
                y2 = st.number_input("Sağ Alt Y", value=170)
            with c3:
                x3 = st.number_input("Sağ Üst X", value=800)
                y3 = st.number_input("Sağ Üst Y", value=355)
            with c4:
                x4 = st.number_input("Sol Üst X", value=320)
                y4 = st.number_input("Sol Üst Y", value=355)

        poligon = [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]

        # Parametreler
        col_slider1, col_slider2 = st.columns(2)
        with col_slider1:
            irtifa = st.slider("Uçuş İrtifası (m)", min_value=30, max_value=120, value=50, step=5)
        with col_slider2:
            binisme = st.slider("Binişme Oranı (%)", min_value=50, max_value=90, value=70, step=5)

        tarla_genisligi = 1000
        tarla_uzunlugu = 500

        # FOV (Görüş Açısı) Hesaplama
        kamera_gorus_acisi = 1.5 
        kapsama = irtifa * kamera_gorus_acisi
        adim = kapsama * (1 - (binisme / 100.0))
        if adim < 5: adim = 5 

        # KUSURSUZ SINIR KENETLENME ALGORİTMASI (Kamera taşmasını %100 engeller)
        tarla_min_x = min(p[0] for p in poligon)
        tarla_max_x = max(p[0] for p in poligon)
        tarla_min_y = min(p[1] for p in poligon)
        tarla_max_y = max(p[1] for p in poligon)

        # Kameranın sığması için gereken güvenli iç sınırlar
        guvenli_min_x = tarla_min_x + (kapsama / 2)
        guvenli_max_x = tarla_max_x - (kapsama / 2)
        guvenli_min_y = tarla_min_y + (kapsama / 2)
        guvenli_max_y = tarla_max_y - (kapsama / 2)

        wp_x, wp_y = [], []
        
        # Eğer irtifa çok yüksekse ve kamera tarladan büyükse hata vermemesi için koruma
        if guvenli_min_x <= guvenli_max_x and guvenli_min_y <= guvenli_max_y:
            mevcut_y = guvenli_min_y
            yon = 1 

            while mevcut_y <= guvenli_max_y + 0.1:
                satir_x = []
                mx = guvenli_min_x
                
                while mx <= guvenli_max_x + 0.1:
                    satir_x.append(mx)
                    mx += adim
                    
                # Kenarda boşluk kalmasın diye tam sınıra son noktayı çakıyoruz!
                if abs(satir_x[-1] - guvenli_max_x) > 1.0:
                    satir_x.append(guvenli_max_x)

                if yon == -1:
                    satir_x.reverse()
                    
                for nx in satir_x:
                    wp_x.append(nx)
                    wp_y.append(mevcut_y)

                mevcut_y += adim
                yon *= -1 
        else:
            st.error("⚠️ İrtifa çok yüksek! Kamera ayak izi tarladan büyük olduğu için rota çizilemiyor. Lütfen irtifayı düşürün.")

        # Metrikler
        toplam_waypoint = len(wp_x)
        toplam_mesafe = sum(((wp_x[i]-wp_x[i-1])**2 + (wp_y[i]-wp_y[i-1])**2)**0.5 for i in range(1, len(wp_x))) if wp_x else 0
        tahmini_sure = (toplam_mesafe / 5) / 60 if toplam_waypoint > 0 else 0

        # PLOTLY ÇİZİMİ
        fig = go.Figure()

        # 1. Arka Plan Uydu Görüntüsü
        if GITHUB_GELISTIRME_MODE:
            fig.add_layout_image(dict(
                source=SENIN_GITHUB_RESIM_LINKIN, 
                xref="x", yref="y", x=0, y=tarla_uzunlugu, sizex=tarla_genisligi, sizey=tarla_uzunlugu,
                sizing="stretch", opacity=0.9, layer="below"
            ))

        # 2. Seçilen Tarlanın Kesin Sınırları (Turkuaz - Trace 0)
        poligon_x = [tarla_min_x, tarla_max_x, tarla_max_x, tarla_min_x, tarla_min_x]
        poligon_y = [tarla_min_y, tarla_min_y, tarla_max_y, tarla_max_y, tarla_min_y]
        fig.add_trace(go.Scatter(
            x=poligon_x, y=poligon_y, mode='lines',
            fill='toself', fillcolor='rgba(0, 229, 255, 0.1)',
            line=dict(color='cyan', width=2, dash="dash"),
            name="Seçilen Tarla Alanı", hoverinfo='skip'
        ))

        if wp_x and wp_y:
            # 3. Uçuş Rotası (Sarı Çizgiler - Trace 1)
            fig.add_trace(go.Scatter(x=wp_x, y=wp_y, mode='lines', line=dict(color='yellow', width=2), hoverinfo='skip'))
            
            # 4. Waypointler (Mavi Noktalar - Trace 2)
            fig.add_trace(go.Scatter(x=wp_x, y=wp_y, mode='markers', marker=dict(color='cyan', size=5), hoverinfo='skip'))

            def b_x(cx, w): return [cx-w/2, cx+w/2, cx+w/2, cx-w/2, cx-w/2]
            def b_y(cy, w): return [cy-w/2, cy-w/2, cy+w/2, cy+w/2, cy-w/2]

            # 5. Kamera Kapsama Alanı (Mavi Kutu - Trace 3)
            fig.add_trace(go.Scatter(
                x=b_x(wp_x[0], kapsama), y=b_y(wp_y[0], kapsama),
                fill='toself', fillcolor='rgba(0, 229, 255, 0.3)', 
                line=dict(color='cyan', width=2, dash='dot'), hoverinfo='skip'
            ))

            # 6. Drone Simgesi (Trace 4)
            fig.add_trace(go.Scatter(x=[wp_x[0]], y=[wp_y[0]], mode='text', text=['🚁'], textfont=dict(size=35), hoverinfo='skip'))

            # Animasyon Kareleri
            frames = [go.Frame(data=[
                go.Scatter(x=b_x(wp_x[i], kapsama), y=b_y(wp_y[i], kapsama)),
                go.Scatter(x=[wp_x[i]], y=[wp_y[i]])
            ], traces=[3, 4]) for i in range(len(wp_x))]
            fig.frames = frames

            fig.update_layout(updatemenus=[dict(
                type="buttons", showactive=False, x=0.5, y=1.15, xanchor="center", yanchor="bottom", direction="left",
                buttons=[
                    dict(label="▶️ Otonom Uçuşu Başlat", method="animate", args=[None, dict(frame=dict(duration=300, redraw=False), transition=dict(duration=300, easing="linear"), fromcurrent=True, mode="immediate")]),
                    dict(label="⏸️ Durdur", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
                ]
            )])

        # Kamera Zoom Mekanizması
        zoom = (irtifa - 30) * 1.5 
        fig.update_layout(
            xaxis=dict(range=[-zoom, tarla_genisligi + zoom], showgrid=False, zeroline=False, visible=False),
            yaxis=dict(range=[-zoom, tarla_uzunlugu + zoom], scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, visible=False),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=50, b=0), height=450, showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        met1, met2, met3 = st.columns(3)
        met1.metric("📌 Toplam Waypoint", f"{toplam_waypoint} Adet")
        met2.metric("📏 Toplam Rota Uzunluğu", f"{int(toplam_mesafe)} Metre")
        met3.metric("⏱️ Tahmini Uçuş Süresi", f"{tahmini_sure:.1f} Dakika")
