"""Control de flota: disponibilidad (días fuera de taller) y días trabajados (días con viaje)."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import calculos as calc
from core import datos
from core.estilo import (CONFIG_GRAFICO, GRIS_CLARO, GRIS_OSCURO, NEGRO, ROJO, encabezado,
                         estado, estilo_grafico, filtro_periodo, leyenda_semaforo, pie,
                         tarjeta_kpi, texto_estado)
from core.formato import MESES_CORTO, fmt_num, mes_anio

encabezado("Tablero de Operaciones — Control de flota",
           f"Datos actualizados al {datos.fecha_actualizacion()} · Datos ilustrativos")

hoy = date.today()
a_def, m_def = calc.mes_anterior(hoy.year, hoy.month)
anio, mes = filtro_periodo("flota", anio_def=a_def, mes_def=m_def)

ed = datos.estado_diario()
patentes = sorted(ed["patente"].unique())
sel = st.multiselect("Camión", patentes, placeholder="Todos los camiones")
if sel:
    ed = ed[ed["patente"].isin(sel)]

META_D, META_T = datos.METAS["disponibilidad"], datos.METAS["dias_trabajados"]
a_ant, m_ant = calc.mes_anterior(anio, mes)
r, r_ant = calc.flota_mes(ed, anio, mes), calc.flota_mes(ed, a_ant, m_ant)

if not r["dias_totales"]:
    st.info("No hay datos para el período seleccionado.")
    st.stop()

# --------------------------------------------------------------- tarjetas
k1, k2, k3, k4 = st.columns(4)
with k1:
    tarjeta_kpi("% Disponibilidad de flota", r["disponibilidad"], "%", meta=META_D,
                delta=r["disponibilidad"] - r_ant["disponibilidad"] if r_ant["disponibilidad"] else None)
with k2:
    tarjeta_kpi("% Días trabajados", r["dias_trabajados"], "%", meta=META_T,
                delta=r["dias_trabajados"] - r_ant["dias_trabajados"] if r_ant["dias_trabajados"] else None)
with k3:
    tarjeta_kpi("Días en taller (camión-día)", r["dias_taller"], "", dec=0, sentido="menor_mejor",
                delta=r["dias_taller"] - r_ant["dias_taller"])
with k4:
    libres = r["dias_disponibles"] - r["dias_con_viaje"]
    tarjeta_kpi("Días disponibles sin viaje", libres, "", dec=0, nota="Capacidad no utilizada")

# --------------------------------------------------------------- tendencia 12 meses
fin = pd.Period(year=anio, month=mes, freq="M")
filas = []
for p in pd.period_range(fin - 11, fin, freq="M"):
    x = calc.flota_mes(ed, p.year, p.month)
    filas.append({"mes": f"{MESES_CORTO[p.month - 1]}-{p.year}", **x})
tend = pd.DataFrame(filas).dropna(subset=["disponibilidad"])

f = go.Figure()
f.add_scatter(x=tend["mes"], y=tend["disponibilidad"], name="% Disponibilidad",
              mode="lines+markers", line=dict(color=NEGRO, width=3))
f.add_scatter(x=tend["mes"], y=tend["dias_trabajados"], name="% Días trabajados",
              mode="lines+markers", line=dict(color=GRIS_OSCURO, width=2, dash="dot"))
f.add_hline(y=META_D, line_dash="dash", line_color=NEGRO, line_width=1,
            annotation_text=f"Meta disponibilidad {fmt_num(META_D, 0)} %", annotation_position="top left")
f.add_hline(y=META_T, line_dash="dash", line_color=GRIS_OSCURO, line_width=1,
            annotation_text=f"Meta días trabajados {fmt_num(META_T, 0)} %",
            annotation_position="bottom left")
f.update_layout(title="Disponibilidad y días trabajados (%) — últimos 12 meses")
f.update_yaxes(range=[70, 100], ticksuffix=" %")
st.plotly_chart(estilo_grafico(f, 360), use_container_width=True, config=CONFIG_GRAFICO)

# --------------------------------------------------------------- calendario
st.subheader(f"Estado diario por camión — {mes_anio(anio, mes)}")
st.markdown(
    f"<span style='color:{GRIS_CLARO};font-size:18px;-webkit-text-stroke:1px #A6A4A3'>■</span> "
    f"Disponible sin viaje &nbsp;&nbsp; <span style='color:{NEGRO};font-size:18px'>■</span> Con viaje "
    f"&nbsp;&nbsp; <span style='color:{ROJO};font-size:18px'>■</span> En taller "
    f"(8 horas o más en OT ese día)", unsafe_allow_html=True)

m = calc.filtrar_mes(ed, anio, mes).copy()
m["dia"] = pd.to_datetime(m["fecha"]).dt.day
m["codigo"] = 0
m.loc[m["con_viaje"] == 1, "codigo"] = 1
m.loc[m["en_taller"] == 1, "codigo"] = 2
por_camion = pd.Series({p: calc.resumen_flota(g)["disponibilidad"] for p, g in m.groupby("patente")}
                       ).sort_values(ascending=False)
z = m.pivot(index="patente", columns="dia", values="codigo").reindex(por_camion.index)
h = m.pivot(index="patente", columns="dia", values="horas_taller").reindex(por_camion.index)
textos = {0: "Disponible sin viaje", 1: "Con viaje", 2: "En taller"}
hover = [[f"{p} · día {d}<br>{textos.get(z.loc[p, d], '—')}<br>Horas en taller: {fmt_num(h.loc[p, d], 1)}"
          if pd.notna(z.loc[p, d]) else "" for d in z.columns] for p in z.index]
cal = go.Figure(go.Heatmap(
    z=z.values, x=z.columns, y=z.index, zmin=0, zmax=2, showscale=False, xgap=1, ygap=1,
    colorscale=[[0, GRIS_CLARO], [0.333, GRIS_CLARO], [0.334, NEGRO], [0.666, NEGRO],
                [0.667, ROJO], [1, ROJO]],
    text=hover, hoverinfo="text"))
cal.update_xaxes(title="Día", dtick=1, side="top")
cal.update_yaxes(title=None, autorange="reversed")
st.plotly_chart(estilo_grafico(cal, max(300, 18 * len(z) + 80)), use_container_width=True,
                config=CONFIG_GRAFICO)
st.caption("Camiones ordenados de menor a mayor disponibilidad (abajo los más afectados).")

# --------------------------------------------------------------- tabla
filas = []
for p, g in m.groupby("patente"):
    x = calc.resumen_flota(g)
    e1, e2 = estado(x["disponibilidad"], META_D), estado(x["dias_trabajados"], META_T)
    peor = max([e1, e2], key=lambda k: {"sin_meta": -1, "cumple": 0, "alerta": 1, "no_cumple": 2}[k])
    filas.append({"Patente": p, "Días totales": x["dias_totales"], "Días en taller": x["dias_taller"],
                  "Días disponibles": x["dias_disponibles"], "Días con viaje": x["dias_con_viaje"],
                  "% Disponibilidad": x["disponibilidad"], "% Días trabajados": x["dias_trabajados"],
                  "Estado": texto_estado(peor)})
st.subheader("Resumen por camión")
st.dataframe(pd.DataFrame(filas).sort_values("% Disponibilidad"), hide_index=True,
             use_container_width=True, column_config={
                 "% Disponibilidad": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100),
                 "% Días trabajados": st.column_config.ProgressColumn(format="%.1f %%", min_value=0, max_value=100)})

leyenda_semaforo()
pie("Disponibilidad = días fuera de taller / días totales. Días trabajados = días con viaje / días "
    "disponibles. Variaciones contra el mes anterior. Metas referenciales por validar. "
    "Datos ilustrativos.")
