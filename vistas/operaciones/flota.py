"""Flota en tiempo real: mapa GPS + estado del ERP, con actualización automática."""
from datetime import datetime

import pandas as pd
import pydeck as pdk
import streamlit as st

from core import datos
from core.estilo import (BLANCO, GRIS_MEDIO, GRIS_OSCURO, NEGRO, ROJO, VERDE,
                         conteo, encabezado, pie)

ESTADOS = {  # clave: (texto, color hex, color RGB para pydeck)
    "en_viaje":  ("En viaje", NEGRO, [32, 28, 25]),
    "en_base":   ("En base, disponible", VERDE, [30, 157, 81]),
    "en_taller": ("En taller", ROJO, [242, 31, 45]),
    "sin_senal": ("Sin señal GPS (más de 30 min)", GRIS_MEDIO, [166, 164, 163]),
}

encabezado("Tablero de Operaciones — Flota en tiempo real",
           "Posición según el GPS · Estado según el ERP (viaje u OT abiertos) · Datos ilustrativos")

f1, f2, _ = st.columns([3, 2, 3])
sel = f1.multiselect("Estado", list(ESTADOS), default=list(ESTADOS),
                     format_func=lambda k: ESTADOS[k][0])
buscar = f2.text_input("Buscar patente", placeholder="Ej.: KTRS-41").strip().upper()


@st.fragment(run_every="30s")
def panel():
    df = datos.estado_actual()
    df = df[df["estado"].isin(sel)]
    if buscar:
        df = df[df["patente"].str.contains(buscar, regex=False)]

    st.caption(f"Última actualización: {datetime.now():%H:%M:%S} · se actualiza cada 30 segundos")

    cols = st.columns(4)
    for col, (k, (texto, color, _)) in zip(cols, ESTADOS.items()):
        with col:
            conteo(texto, int((df["estado"] == k).sum()), color)

    # ---------------------------------------------------------- mapa
    mapa_col, ley_col = st.columns([5, 1])
    d = df.copy()
    d["color"] = d["estado"].map(lambda k: ESTADOS[k][2])
    d["texto_estado"] = d["estado"].map(lambda k: ESTADOS[k][0])
    d["hora"] = pd.to_datetime(d["ultima_posicion"]).dt.strftime("%H:%M")
    capa = pdk.Layer(
        "ScatterplotLayer",
        # solo columnas simples: pydeck no serializa fechas
        data=d[["lon", "lat", "color", "patente", "texto_estado", "conductor", "viaje", "hora"]],
        get_position="[lon, lat]", get_fill_color="color",
        get_line_color=[255, 254, 254], line_width_min_pixels=1, stroked=True,
        radius_min_pixels=6, radius_max_pixels=10, get_radius=3000, pickable=True,
    )
    vista = pdk.ViewState(latitude=-27.5, longitude=-70.8, zoom=4.5)
    tooltip = {"html": "<b>{patente}</b><br/>{texto_estado}<br/>{conductor}<br/>"
                       "Viaje: {viaje}<br/>Última posición: {hora}",
               "style": {"backgroundColor": BLANCO, "color": NEGRO, "fontSize": "12px"}}
    with mapa_col:
        st.pydeck_chart(pdk.Deck(layers=[capa], initial_view_state=vista, tooltip=tooltip,
                                 map_style="light"), height=520)
    with ley_col:
        st.markdown("**Leyenda**")
        for texto, color, _ in ESTADOS.values():
            st.markdown(f"<span style='color:{color};font-size:18px'>●</span> {texto}",
                        unsafe_allow_html=True)
        st.caption("Pase el cursor sobre un punto para ver el detalle.")

    # ---------------------------------------------------------- tabla
    st.subheader("Detalle por camión")
    orden = {"en_base": 0, "en_viaje": 1, "en_taller": 2, "sin_senal": 3}
    t = d.sort_values(by="estado", key=lambda s: s.map(orden))
    t = pd.DataFrame({
        "Patente": t["patente"],
        "Estado": "● " + t["texto_estado"],
        "Conductor": t["conductor"],
        "Viaje actual": t["viaje"],
        "Cliente": t["cliente"],
        "Última posición": t["hora"],
        "Última carga de combustible": t["ultima_carga"],
        "OT abierta": t["ot_abierta"],
    })
    st.dataframe(t, hide_index=True, use_container_width=True, height=420)


panel()

st.caption("El proveedor de GPS conserva cerca de 24 horas de historial; las posiciones se "
           "registrarán en el data warehouse para análisis posterior.")
pie("Primero aparecen los camiones disponibles en base, para asignar. Datos ilustrativos.")
