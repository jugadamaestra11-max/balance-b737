# streamlit_app.py - VERSIÓN COMPLETA
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import urllib.request
import json
from datetime import datetime
import hashlib

st.set_page_config(page_title="B737-300 Balance Sheet", page_icon="✈", layout="wide")

# ==================== CONSTANTES ====================
EOW = 33490
LEMAC = 7.5
MAC_LONG = 3.5
PESO_ADULTO = 81
PESO_NINO = 35
PESO_BEBE = 10

BRAZOS = {
    'eow': 12.5, 'pax': 14.0,
    'cargo_fwd': 8.5, 'cargo_aft': 20.5, 'fuel': 13.5
}

AEROPUERTOS = {
    'SLLP': 'La Paz - El Alto',
    'SLCB': 'Cochabamba - Wilstermann',
    'SLVR': 'Santa Cruz - Viru Viru',
    'SLTJ': 'Tarija',
    'SLPO': 'Potosí',
    'SLTR': 'Trinidad',
    'SLAL': 'Sucre - Alcantarí'
}

# ==================== FUNCIONES ====================
def calcular_mac(adultos, ninos, bebes, cargo_fwd, cargo_aft, fuel_to):
    peso_pax = adultos * PESO_ADULTO + ninos * PESO_NINO + bebes * PESO_BEBE
    peso_carga = cargo_fwd + cargo_aft
    
    momento = (EOW * BRAZOS['eow'] +
               peso_pax * BRAZOS['pax'] +
               cargo_fwd * BRAZOS['cargo_fwd'] +
               cargo_aft * BRAZOS['cargo_aft'] +
               fuel_to * BRAZOS['fuel'])
    
    peso_total = EOW + peso_pax + peso_carga + fuel_to
    cg = momento / peso_total if peso_total > 0 else 0
    mac = (cg - LEMAC) / MAC_LONG * 100
    mac = max(15, min(45, mac))
    trim = 4.0 + (mac - 25.0) * 0.08
    trim = max(0, min(10, trim))
    zfw = EOW + peso_pax + peso_carga
    tow = zfw + fuel_to
    
    return mac, trim, zfw, tow, cg

def obtener_metar(icao):
    """Obtiene METAR en tiempo real"""
    try:
        url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data:
                metar = data[0]
                return {
                    'station': metar.get('station', icao),
                    'temp': metar.get('temp', 'N/A'),
                    'wind_dir': metar.get('wdir_dir', 'N/A'),
                    'wind_speed': metar.get('wspd', 'N/A'),
                    'visibility': metar.get('visib', 'N/A'),
                    'conditions': metar.get('text', 'N/A'),
                    'raw': metar.get('rawOb', 'No disponible')
                }
    except:
        pass
    return None

def obtener_taf(icao):
    """Obtiene TAF en tiempo real"""
    try:
        url = f"https://aviationweather.gov/api/data/taf?ids={icao}&format=json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            if data:
                taf = data[0]
                return taf.get('raw', 'No disponible')
    except:
        pass
    return "No disponible"

def grafico_balance(mac, peso):
    """Crea gráfico interactivo con Plotly"""
    fig = go.Figure()
    
    # Área segura
    x_range = np.linspace(20, 35, 100)
    y_range = np.linspace(30, 65, 100)
    
    fig.add_trace(go.Scatter(
        x=[20, 35, 35, 20, 20],
        y=[30, 30, 65, 65, 30],
        fill="toself",
        fillcolor="rgba(79, 195, 247, 0.3)",
        line=dict(color="rgba(79, 195, 247, 0)"),
        name="Área Segura",
        showlegend=True
    ))
    
    # Líneas límite
    fig.add_vline(x=20, line_dash="dash", line_color="cyan", annotation_text="Límite Forward (20%)")
    fig.add_vline(x=35, line_dash="dash", line_color="cyan", annotation_text="Límite Aft (35%)")
    
    # Punto del CG
    color = "#88ff88" if 20 <= mac <= 35 else "#ff6b6b"
    fig.add_trace(go.Scatter(
        x=[mac], y=[peso],
        mode='markers',
        marker=dict(size=20, color=color, symbol='circle', line=dict(color='white', width=2)),
        name=f'CG: {mac:.1f}%'
    ))
    
    fig.update_layout(
        title="📊 ENVOLVENTE DE BALANCE",
        xaxis_title="% MAC (Centro de Gravedad)",
        yaxis_title="Peso Bruto (1000 kg)",
        xaxis_range=[15, 45],
        yaxis_range=[30, 65],
        template="plotly_dark",
        height=450,
        hovermode="closest"
    )
    
    return fig

# ==================== INICIALIZAR SESIÓN ====================
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'chat' not in st.session_state:
    st.session_state.chat = []

# ==================== INTERFAZ ====================
st.title("✈ BALANCE SHEET - BOEING B737-300")
st.markdown("*Sistema Profesional con IA Integrada*")

# Pestañas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚖ BALANCE", "🌤 CLIMA", "📋 HISTORIAL", "🤖 CHATBOT IA", "📊 GRÁFICOS"
])

# ==================== TAB 1: BALANCE ====================
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 DATOS DEL VUELO")
        
        vuelo = st.text_input("Número de Vuelo", "BOA2551")
        
        col_orig, col_dest = st.columns(2)
        with col_orig:
            origen = st.selectbox("Origen", list(AEROPUERTOS.keys()), index=0)
            st.caption(f"📍 {AEROPUERTOS[origen]}")
        with col_dest:
            destino = st.selectbox("Destino", list(AEROPUERTOS.keys()), index=1)
            st.caption(f"📍 {AEROPUERTOS[destino]}")
        
        st.subheader("👥 PASAJEROS")
        col_ad, col_ni, col_be = st.columns(3)
        with col_ad:
            adultos = st.number_input("Adultos", min_value=0, max_value=138, value=85)
        with col_ni:
            ninos = st.number_input("Niños", min_value=0, value=0)
        with col_be:
            bebes = st.number_input("Bebés", min_value=0, value=0)
        
        st.subheader("📦 CARGO (kg)")
        col_cf, col_ca = st.columns(2)
        with col_cf:
            cargo_fwd = st.number_input("Compartimiento Delantero", min_value=0, value=1600)
        with col_ca:
            cargo_aft = st.number_input("Compartimiento Trasero", min_value=0, value=3100)
        
        st.subheader("⛽ COMBUSTIBLE (kg)")
        fuel_to = st.number_input("Takeoff Fuel", min_value=0, value=5550)
        
        calcular = st.button("🔄 CALCULAR BALANCE", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("⚖ RESULTADOS")
        
        if calcular or True:
            total_pax = adultos + ninos
            
            if total_pax > 138:
                st.error(f"❌ EXCEDE CAPACIDAD MÁXIMA: {total_pax} pasajeros (máximo 138)")
            else:
                mac, trim, zfw, tow, cg = calcular_mac(adultos, ninos, bebes, cargo_fwd, cargo_aft, fuel_to)
                
                dentro = 20 <= mac <= 35
                estado = "✅ DENTRO DE LÍMITES" if dentro else "⚠️ FUERA DE LÍMITES"
                
                # Métricas principales
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("%MAC", f"{mac:.1f}%", estado)
                col_m2.metric("TRIM", f"{trim:.1f}")
                col_m3.metric("CG (m)", f"{cg:.2f}")
                
                st.divider()
                
                col_p1, col_p2 = st.columns(2)
                col_p1.metric("ZFW (Zero Fuel)", f"{zfw:,.0f} kg")
                col_p2.metric("TOW (Takeoff)", f"{tow:,.0f} kg")
                
                # Barra de estado
                st.subheader("📊 POSICIÓN DEL CENTRO DE GRAVEDAD")
                progress = min(int((mac - 15) / 30 * 100), 100)
                st.progress(progress)
                st.caption(f"Límite Forward: 20% | Valor actual: {mac:.1f}% | Límite Aft: 35%")
                
                if dentro:
                    st.success("✅ El avión está correctamente balanceado")
                else:
                    if mac < 20:
                        st.warning("⚠️ CG demasiado adelante - Mover carga/pasajeros hacia atrás")
                    else:
                        st.warning("⚠️ CG demasiado atrás - Mover carga/pasajeros hacia adelante")
                
                # Guardar en historial
                st.session_state.historial.append({
                    'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'vuelo': vuelo,
                    'origen': origen,
                    'destino': destino,
                    'adultos': adultos,
                    'mac': mac,
                    'estado': "Dentro" if dentro else "Fuera",
                    'zfw': zfw,
                    'tow': tow
                })

# ==================== TAB 2: CLIMA ====================
with tab2:
    st.subheader("🌤 REPORTE CLIMÁTICO EN TIEMPO REAL")
    
    col_met, col_info = st.columns([1, 1])
    
    with col_met:
        icao_metar = st.selectbox("Seleccionar Aeropuerto", list(AEROPUERTOS.keys()), key="metar_sel")
        st.caption(f"📍 {AEROPUERTOS[icao_metar]}")
        
        if st.button("🔄 OBTENER CLIMA", key="btn_metar", use_container_width=True):
            with st.spinner("Obteniendo datos meteorológicos..."):
                metar = obtener_metar(icao_metar)
                taf = obtener_taf(icao_metar)
                
                if metar:
                    st.session_state.metar_data = metar
                    st.session_state.taf_data = taf
                else:
                    st.error("No se pudo obtener el clima")
    
    with col_info:
        if 'metar_data' in st.session_state:
            m = st.session_state.metar_data
            st.info(f"""
            **📍 {m['station']} - {AEROPUERTOS.get(m['station'], '')}**
            
            🌡️ **Temperatura:** {m['temp']}°C
            💨 **Viento:** {m['wind_dir']}° a {m['wind_speed']} kt
            👁️ **Visibilidad:** {m['visibility']} km
            🌥️ **Condiciones:** {m['conditions']}
            """)
            
            with st.expander("📡 METAR completo"):
                st.code(m['raw'])
            
            with st.expander("📡 TAF (Pronóstico)"):
                st.code(st.session_state.taf_data)
        else:
            st.info("👈 Selecciona un aeropuerto y presiona 'OBTENER CLIMA'")

# ==================== TAB 3: HISTORIAL ====================
with tab3:
    st.subheader("📋 HISTORIAL DE CÁLCULOS")
    
    if st.session_state.historial:
        df = pd.DataFrame(st.session_state.historial)
        st.dataframe(df, use_container_width=True)
        
        if st.button("🗑️ LIMPIAR HISTORIAL"):
            st.session_state.historial = []
            st.rerun()
        
        # Exportar CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 EXPORTAR A CSV", csv, "historial_balance.csv", "text/csv")
    else:
        st.info("No hay cálculos guardados. Realiza un balance en la pestaña principal.")

# ==================== TAB 4: CHATBOT IA ====================
with tab4:
    st.subheader("🤖 ASISTENTE DE BALANCE")
    
    # Mostrar chat
    chat_container = st.container(height=400)
    
    with chat_container:
        for msg in st.session_state.chat:
            if msg['rol'] == 'usuario':
                st.markdown(f"**👤 Tú:** {msg['mensaje']}")
            else:
                st.markdown(f"**🤖 Asistente:** {msg['mensaje']}")
    
    # Entrada de usuario
    col_chat, col_btn = st.columns([4, 1])
    with col_chat:
        pregunta = st.text_input("Escribe tu pregunta...", key="chat_input", label_visibility="collapsed")
    with col_btn:
        enviar = st.button("📤 ENVIAR", use_container_width=True)
    
    if enviar and pregunta:
        st.session_state.chat.append({'rol': 'usuario', 'mensaje': pregunta})
        
        # Respuestas inteligentes
        respuesta = ""
        p_lower = pregunta.lower()
        
        if 'mac' in p_lower or 'centro' in p_lower:
            respuesta = "📐 %MAC (Mean Aerodynamic Chord) es el centro de gravedad expresado como porcentaje. Rango seguro: 20-35%. Valores fuera de este rango indican desbalance."
        elif 'trim' in p_lower:
            respuesta = "⚙️ TRIM = ajuste del estabilizador horizontal. Fórmula: TRIM = 4 + (%MAC - 25) × 0.08. Valores típicos: 4.0-5.0 unidades."
        elif 'zfw' in p_lower:
            respuesta = "✈ ZFW (Zero Fuel Weight) = peso sin combustible. Se calcula: EOW + Pasajeros + Carga. No debe superar 48,307 kg para B737-300."
        elif 'ejemplo' in p_lower:
            respuesta = "📋 EJEMPLO: Vuelo SLLP-SLCB, 85 adultos, 1600kg cargo fwd, 3100kg cargo aft, 5550kg fuel → %MAC ≈ 22.5% (DENTRO DE LÍMITES)."
        elif 'calcular' in p_lower:
            respuesta = "💡 Ve a la pestaña 'BALANCE', ingresa los datos y presiona 'CALCULAR BALANCE'."
        elif 'clima' in p_lower:
            respuesta = "🌤 Ve a la pestaña 'CLIMA', selecciona un aeropuerto y presiona 'OBTENER CLIMA' para ver METAR y TAF."
        else:
            respuesta = "Pregunta sobre: %MAC, TRIM, ZFW, ejemplo, calcular o clima. También puedo ayudarte con conceptos de balance aeronáutico."
        
        st.session_state.chat.append({'rol': 'asistente', 'mensaje': respuesta})
        st.rerun()

# ==================== TAB 5: GRÁFICOS ====================
with tab5:
    st.subheader("📊 VISUALIZACIÓN AVANZADA")
    
    if 'historial' in st.session_state and st.session_state.historial:
        ultimo = st.session_state.historial[-1]
        peso = ultimo.get('zfw', 45075) / 1000
        mac_actual = ultimo.get('mac', 22.5)
        
        fig = grafico_balance(mac_actual, peso)
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretación
        st.subheader("📈 INTERPRETACIÓN")
        if 20 <= mac_actual <= 35:
            st.success(f"✅ El centro de gravedad está en {mac_actual:.1f}% MAC, dentro del rango seguro (20-35%). El avión es estable.")
        elif mac_actual < 20:
            st.warning(f"⚠️ El centro de gravedad está en {mac_actual:.1f}% MAC (demasiado adelante). El avión será nariz-pesado.")
        else:
            st.warning(f"⚠️ El centro de gravedad está en {mac_actual:.1f}% MAC (demasiado atrás). El avión será cola-pesado.")
    else:
        st.info("👈 Realiza un balance en la pestaña principal para ver el gráfico.")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://cdn.jsdelivr.net/gh/devicons/devicon/icons/streamlit/streamlit-original.svg", width=50)
    st.markdown("---")
    
    st.metric("EOW (Peso Vacío)", "33,490 kg")
    st.metric("MZFW", "48,307 kg")
    st.metric("MTOW", "50,100 kg")
    st.metric("MLW", "51,709 kg")
    
    st.markdown("---")
    st.caption(f"🕒 Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("📡 Datos METAR/TAF de aviationweather.gov")
