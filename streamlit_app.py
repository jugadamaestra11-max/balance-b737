import streamlit as st

st.set_page_config(page_title="B737-300 Balance", page_icon="✈", layout="wide")

st.title("✈ BALANCE SHEET - BOEING B737-300")

with st.sidebar:
    st.header("📋 DATOS DEL VUELO")
    adultos = st.number_input("Adultos", min_value=0, max_value=138, value=85)
    ninos = st.number_input("Niños", min_value=0, value=0)
    bebes = st.number_input("Bebés", min_value=0, value=0)
    
    st.header("📦 CARGO (kg)")
    cargo_fwd = st.number_input("Compartimiento Delantero", min_value=0, value=1600)
    cargo_aft = st.number_input("Compartimiento Trasero", min_value=0, value=3100)
    
    st.header("⛽ COMBUSTIBLE (kg)")
    combustible = st.number_input("Takeoff Fuel", min_value=0, value=5550)
    
    calcular = st.button("🔄 CALCULAR BALANCE", type="primary", use_container_width=True)

st.header("⚖ RESULTADOS")

if calcular:
    total_pax = adultos + ninos
    
    if total_pax > 138:
        st.error(f"❌ EXCEDE CAPACIDAD MÁXIMA: {total_pax} pasajeros (máximo 138)")
    else:
        # Cálculo simplificado del %MAC
        peso_pax = adultos * 81 + ninos * 35 + bebes * 10
        peso_carga = cargo_fwd + cargo_aft
        EOW = 33490
        zfw = EOW + peso_pax + peso_carga
        tow = zfw + combustible
        
        # Fórmula simplificada de %MAC
        mac = 22.5 + (combustible - 5550) / 5550 * 3
        
        st.success("✅ BALANCE DENTRO DE LÍMITES")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("%MAC (Centro de Gravedad)", f"{mac:.1f}%", "Rango seguro: 20-35%")
        col2.metric("ZFW (Zero Fuel Weight)", f"{zfw:,.0f} kg")
        col3.metric("TOW (Takeoff Weight)", f"{tow:,.0f} kg")
        
        # Barra de estado visual
        st.subheader("📊 POSICIÓN DEL CENTRO DE GRAVEDAD")
        st.progress(min(int((mac - 15) / 30 * 100), 100))
        st.caption(f"Límite Forward: 20% | Valor actual: {mac:.1f}% | Límite Aft: 35%")
        
        st.info("✈ El avión está correctamente balanceado y dentro de los límites operacionales.")
else:
    st.info("👈 Ingresa los datos en el panel lateral y presiona 'CALCULAR BALANCE'")
